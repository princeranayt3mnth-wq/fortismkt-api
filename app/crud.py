from enum import Enum

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    ListingPaymentMethod,
    SocialAccountListing,
)
from app.schemas import ListingCreate, ListingUpdate
from sqlalchemy import (
    func,
    select,
)
from sqlalchemy.orm import Session

from app.models import Review
from app.schemas import (
    ReviewCreate,
    ReviewUpdate,
)

def get_listing(
    db: Session,
    listing_id: int,
) -> SocialAccountListing | None:
    statement = (
        select(SocialAccountListing)
        .where(SocialAccountListing.id == listing_id)
        .options(
            selectinload(
                SocialAccountListing.payment_methods
            ),
            selectinload(
                SocialAccountListing.screenshots
            ),
        )
    )

    return db.scalar(statement)


def get_listings(
    db: Session,
    page: int,
    page_size: int,
    status_filter: str | None = None,
):
    filters = []

    if status_filter:
        filters.append(
            SocialAccountListing.status == status_filter
        )

    total_statement = (
        select(func.count(SocialAccountListing.id))
        .where(*filters)
    )

    total = db.scalar(total_statement) or 0

    statement = (
        select(SocialAccountListing)
        .where(*filters)
        .options(
            selectinload(
                SocialAccountListing.payment_methods
            ),
            selectinload(
                SocialAccountListing.screenshots
            ),
        )
        .order_by(
            SocialAccountListing.created_at.desc()
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    items = db.scalars(statement).all()

    return items, total


def create_listing(
    db: Session,
    payload: ListingCreate,
    status_value: str = "pending",
) -> SocialAccountListing:
    listing_data = payload.model_dump(
        exclude={"payment_methods"},
    )

    listing_data["platform"] = (
        payload.platform.value
    )

    listing_data["account_url"] = str(
        payload.account_url
    )

    listing = SocialAccountListing(
        **listing_data,
        status=status_value,
    )

    db.add(listing)
    db.flush()

    unique_methods = list(
        dict.fromkeys(payload.payment_methods)
    )

    listing.payment_methods = [
        ListingPaymentMethod(
            payment_method=method.value,
        )
        for method in unique_methods
    ]

    db.flush()

    return listing

def update_listing(
    db: Session,
    listing: SocialAccountListing,
    payload: ListingUpdate,
) -> SocialAccountListing:
    update_data = payload.model_dump(
        exclude_unset=True,
    )

    payment_methods = update_data.pop(
        "payment_methods",
        None,
    )

    for field_name in ("platform", "status"):
        value = update_data.get(field_name)

        if isinstance(value, Enum):
            update_data[field_name] = value.value

    if update_data.get("account_url") is not None:
        update_data["account_url"] = str(
            update_data["account_url"]
        )

    final_monetized = update_data.get(
        "is_monetized",
        listing.is_monetized,
    )

    final_revenue = update_data.get(
        "average_monthly_revenue_usd",
        listing.average_monthly_revenue_usd,
    )

    if final_monetized and final_revenue is None:
        raise ValueError(
            "Revenue is required for a monetized account."
        )

    if not final_monetized:
        update_data[
            "average_monthly_revenue_usd"
        ] = None

    for field_name, value in update_data.items():
        setattr(listing, field_name, value)

    if payment_methods is not None:
        unique_methods = list(
            dict.fromkeys(payment_methods)
        )

        listing.payment_methods.clear()

        listing.payment_methods.extend(
            ListingPaymentMethod(
                payment_method=method.value
            )
            for method in unique_methods
        )

    db.flush()

    return listing



def create_review(
    db: Session,
    payload: ReviewCreate,
) -> Review:
    review_data = payload.model_dump()

    review_data["platform"] = (
        payload.platform.value
    )

    review_data["status"] = (
        payload.status.value
    )

    review = Review(
        **review_data
    )

    db.add(review)
    db.flush()

    return review

def get_review(
    db: Session,
    review_id: int,
) -> Review | None:
    statement = select(Review).where(
        Review.id == review_id
    )

    return db.scalar(statement)


def get_reviews(
    db: Session,
    page: int,
    page_size: int,
    status_filter: str | None = None,
) -> tuple[list[Review], int]:
    filters = []

    if status_filter:
        filters.append(
            Review.status == status_filter
        )

    total_statement = (
        select(func.count(Review.id))
        .where(*filters)
    )

    total = (
        db.scalar(total_statement) or 0
    )

    statement = (
        select(Review)
        .where(*filters)
        .order_by(
            Review.created_at.desc()
        )
        .offset(
            (page - 1) * page_size
        )
        .limit(page_size)
    )

    items = list(
        db.scalars(statement).all()
    )

    return items, total



def update_review(
    db: Session,
    review: Review,
    payload: ReviewUpdate,
) -> Review:
    update_data = payload.model_dump(
        exclude_unset=True
    )

    if (
        "platform" in update_data
        and update_data["platform"] is not None
    ):
        update_data["platform"] = (
            update_data["platform"].value
        )

    if (
        "status" in update_data
        and update_data["status"] is not None
    ):
        update_data["status"] = (
            update_data["status"].value
        )

    for field_name, value in (
        update_data.items()
    ):
        setattr(
            review,
            field_name,
            value,
        )

    db.flush()

    return review