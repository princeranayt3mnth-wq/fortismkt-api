import shutil
from decimal import Decimal
from pathlib import Path
from urllib.parse import quote, urlparse

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.file_storage import (
    UPLOAD_ROOT,
    save_listing_screenshot,
)
from app.models import ListingScreenshot
from app.schemas import (
    ListingCreate,
    ListingResponse,
    ListingStatus,
    ListingUpdate,
    PaginatedListingResponse,
    PaymentMethod,
    Platform,
)


router = APIRouter(
    prefix="/listings",
    tags=["Social Account Listings"],
)


MAX_SCREENSHOTS = 5


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def normalize_optional_text(
    value: str | None,
) -> str | None:
    """
    Removes extra spaces from optional text fields.
    Returns None when the value is empty.
    """
    if value is None:
        return None

    cleaned_value = value.strip()

    return cleaned_value or None


def normalize_username(
    username: str | None,
) -> str | None:
    """
    Converts:
    @username -> username
    """
    if not username:
        return None

    cleaned_username = (
        username
        .strip()
        .lstrip("@")
    )

    return cleaned_username or None


def extract_username_from_url(
    account_url: str | None,
) -> str | None:
    """
    Attempts to extract username from a social profile URL.

    Examples:
    https://instagram.com/testuser -> testuser
    https://youtube.com/@testuser  -> testuser
    """
    if not account_url:
        return None

    try:
        parsed_url = urlparse(account_url)

        path_parts = [
            part
            for part in parsed_url.path.split("/")
            if part
        ]

        if not path_parts:
            return None

        username = (
            path_parts[-1]
            .strip()
            .lstrip("@")
        )

        return username or None

    except (TypeError, ValueError):
        return None


def build_profile_url(
    platform: Platform,
    username: str,
) -> str:
    """
    Builds a profile URL when admin provides username
    but does not provide Profile URL.
    """
    safe_username = quote(
        username.strip().lstrip("@")
    )

    profile_urls = {
        Platform.instagram: (
            f"https://www.instagram.com/{safe_username}"
        ),
        Platform.youtube: (
            f"https://www.youtube.com/@{safe_username}"
        ),
        Platform.tiktok: (
            f"https://www.tiktok.com/@{safe_username}"
        ),
        Platform.facebook: (
            f"https://www.facebook.com/{safe_username}"
        ),
        Platform.x: (
            f"https://x.com/{safe_username}"
        ),
        Platform.telegram: (
            f"https://t.me/{safe_username}"
        ),
        Platform.linkedin: (
            f"https://www.linkedin.com/in/{safe_username}"
        ),
    }

    return profile_urls.get(
        platform,
        f"https://example.com/{safe_username}",
    )


def remove_saved_files(
    file_paths: list[Path],
) -> None:
    """
    Removes files saved before a database error occurred.
    """
    for file_path in file_paths:
        try:
            file_path.unlink(missing_ok=True)
        except OSError:
            pass


# ============================================================
# CREATE LISTING
# Same API is used by both:
#
# Public form:
# POST /api/v1/listings
# publish_immediately omitted/false -> pending
#
# Admin form:
# POST /api/v1/listings
# publish_immediately=true -> approved
# ============================================================

@router.post(
    "",
    response_model=ListingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_listing(
    # Basic details
    platform: Platform = Form(...),
    username: str | None = Form(None),
    account_url: str | None = Form(None),

    # Followers and reach
    followers_count: int = Form(...),
    reach_last_28_days: int | None = Form(None),
    reach_last_90_days: int | None = Form(None),

    # Account details
    account_age_months: int = Form(0),
    top_country: str | None = Form(None),
    second_top_country: str | None = Form(None),
    third_top_country: str | None = Form(None),
    niche: str | None = Form(None),

    # Monetization
    is_monetized: bool = Form(False),
    average_monthly_revenue_usd: Decimal | None = Form(
        None
    ),

    # Audience information
    audience_male_percentage: Decimal | None = Form(
        None
    ),
    audience_female_percentage: Decimal | None = Form(
        None
    ),

    # Additional account information
    account_created_date_text: str | None = Form(None),
    has_original_email: bool = Form(False),

    # Pricing and escrow
    is_price_negotiable: bool = Form(False),
    is_escrow_accepted: bool = Form(False),
    asking_price_usd: Decimal = Form(...),
    original_price_usd: Decimal | None = Form(None),

    # Marketplace controls
    is_promoted: bool = Form(False),
    is_flash_sale: bool = Form(False),

    # Payment methods and screenshots
    payment_methods: list[PaymentMethod] | None = Form(
        None
    ),
    screenshots: list[UploadFile] | None = File(None),

    # Admin form can send true to publish directly
    publish_immediately: bool = Form(False),

    db: Session = Depends(get_db),
):
    uploaded_screenshots = screenshots or []

    # --------------------------------------------------------
    # Screenshot count validation
    # --------------------------------------------------------

    if len(uploaded_screenshots) > MAX_SCREENSHOTS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Maximum {MAX_SCREENSHOTS} screenshots "
                "are allowed."
            ),
        )

    # --------------------------------------------------------
    # Resolve username and account URL
    # --------------------------------------------------------

    resolved_username = normalize_username(
        username
    )

    resolved_account_url = normalize_optional_text(
        account_url
    )

    if (
        resolved_username is None
        and resolved_account_url is not None
    ):
        resolved_username = extract_username_from_url(
            resolved_account_url
        )

    if (
        resolved_account_url is None
        and resolved_username is not None
    ):
        resolved_account_url = build_profile_url(
            platform=platform,
            username=resolved_username,
        )

    if resolved_account_url is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Either account URL or username "
                "must be provided."
            ),
        )

    # --------------------------------------------------------
    # Validate and prepare Pydantic payload
    # --------------------------------------------------------

    try:
        payload = ListingCreate(
            platform=platform,
            username=resolved_username,
            account_url=resolved_account_url,

            followers_count=followers_count,
            reach_last_28_days=reach_last_28_days,
            reach_last_90_days=reach_last_90_days,

            account_age_months=account_age_months,

            top_country=normalize_optional_text(
                top_country
            ),
            second_top_country=normalize_optional_text(
                second_top_country
            ),
            third_top_country=normalize_optional_text(
                third_top_country
            ),
            niche=normalize_optional_text(
                niche
            ),

            is_monetized=is_monetized,
            average_monthly_revenue_usd=(
                average_monthly_revenue_usd
            ),

            audience_male_percentage=(
                audience_male_percentage
            ),
            audience_female_percentage=(
                audience_female_percentage
            ),

            account_created_date_text=(
                normalize_optional_text(
                    account_created_date_text
                )
            ),
            has_original_email=has_original_email,

            is_price_negotiable=(
                is_price_negotiable
            ),
            is_escrow_accepted=(
                is_escrow_accepted
            ),

            asking_price_usd=asking_price_usd,
            original_price_usd=original_price_usd,

            is_promoted=is_promoted,
            is_flash_sale=is_flash_sale,

            payment_methods=payment_methods or [],
        )

    except ValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=jsonable_encoder(
                error.errors()
            ),
        ) from error

    listing_id: int | None = None
    saved_paths: list[Path] = []

    try:
        # Admin form can publish directly.
        # Public form remains pending.
        listing_status = (
            ListingStatus.approved.value
            if publish_immediately
            else ListingStatus.pending.value
        )

        listing = crud.create_listing(
            db=db,
            payload=payload,
            status_value=listing_status,
        )

        listing_id = listing.id

        # ----------------------------------------------------
        # Save screenshots
        # ----------------------------------------------------

        for uploaded_file in uploaded_screenshots:
            file_data = await save_listing_screenshot(
                upload=uploaded_file,
                listing_id=listing.id,
            )

            absolute_path = file_data.pop(
                "absolute_path"
            )

            saved_paths.append(
                absolute_path
            )

            listing.screenshots.append(
                ListingScreenshot(
                    **file_data
                )
            )

        db.commit()

    except HTTPException:
        db.rollback()

        remove_saved_files(
            saved_paths
        )

        if listing_id is not None:
            shutil.rmtree(
                UPLOAD_ROOT / str(listing_id),
                ignore_errors=True,
            )

        raise

    except IntegrityError as error:
        db.rollback()

        remove_saved_files(
            saved_paths
        )

        if listing_id is not None:
            shutil.rmtree(
                UPLOAD_ROOT / str(listing_id),
                ignore_errors=True,
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Listing could not be submitted "
                "because of a database conflict."
            ),
        ) from error

    except Exception:
        db.rollback()

        remove_saved_files(
            saved_paths
        )

        if listing_id is not None:
            shutil.rmtree(
                UPLOAD_ROOT / str(listing_id),
                ignore_errors=True,
            )

        raise

    created_listing = crud.get_listing(
        db=db,
        listing_id=listing.id,
    )

    if created_listing is None:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Listing was created but could "
                "not be loaded."
            ),
        )

    return created_listing


# ============================================================
# GET ALL LISTINGS
# ============================================================

@router.get(
    "",
    response_model=PaginatedListingResponse,
)
def get_all_listings(
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=10,
        ge=1,
        le=100,
    ),
    listing_status: ListingStatus | None = Query(
        default=None,
        alias="status",
    ),
    db: Session = Depends(get_db),
):
    items, total = crud.get_listings(
        db=db,
        page=page,
        page_size=page_size,
        status_filter=(
            listing_status.value
            if listing_status
            else None
        ),
    )

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ============================================================
# GET LISTING BY ID
# ============================================================

@router.get(
    "/{listing_id}",
    response_model=ListingResponse,
)
def get_listing_by_id(
    listing_id: int,
    db: Session = Depends(get_db),
):
    listing = crud.get_listing(
        db=db,
        listing_id=listing_id,
    )

    if listing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found.",
        )

    return listing


# ============================================================
# UPDATE LISTING
# ============================================================

@router.patch(
    "/{listing_id}",
    response_model=ListingResponse,
)
def update_listing_by_id(
    listing_id: int,
    payload: ListingUpdate,
    db: Session = Depends(get_db),
):
    listing = crud.get_listing(
        db=db,
        listing_id=listing_id,
    )

    if listing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found.",
        )

    try:
        crud.update_listing(
            db=db,
            listing=listing,
            payload=payload,
        )

        db.commit()

    except ValueError as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    except IntegrityError as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Listing could not be updated.",
        ) from error

    updated_listing = crud.get_listing(
        db=db,
        listing_id=listing_id,
    )

    if updated_listing is None:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Listing was updated but could "
                "not be loaded."
            ),
        )

    return updated_listing


# ============================================================
# DELETE LISTING
# ============================================================

@router.delete(
    "/{listing_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_listing_by_id(
    listing_id: int,
    db: Session = Depends(get_db),
):
    listing = crud.get_listing(
        db=db,
        listing_id=listing_id,
    )

    if listing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found.",
        )

    try:
        db.delete(listing)
        db.commit()

    except IntegrityError as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Listing could not be deleted.",
        ) from error

    shutil.rmtree(
        UPLOAD_ROOT / str(listing_id),
        ignore_errors=True,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )