import shutil
from pathlib import Path

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
    REVIEW_UPLOAD_ROOT,
    save_review_screenshot,
)
from app.schemas import (
    PaginatedReviewResponse,
    Platform,
    ReviewCreate,
    ReviewResponse,
    ReviewStatus,
    ReviewUpdate,
)


router = APIRouter(
    prefix="/reviews",
    tags=["Reviews"],
)


def clean_optional_text(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    cleaned_value = value.strip()

    return cleaned_value or None


@router.post(
    "",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_new_review(
    buyer_name: str = Form(...),

    avatar_initial: str | None = Form(
        None
    ),

    platform: Platform = Form(...),

    account_type_label: str | None = Form(
        None
    ),

    rating: int = Form(...),

    review_date_text: str | None = Form(
        None
    ),

    review_text: str = Form(...),

    review_status: ReviewStatus = Form(
        ReviewStatus.published,
        alias="status",
    ),

    screenshot: UploadFile | None = File(
        None
    ),

    db: Session = Depends(get_db),
):
    try:
        payload = ReviewCreate(
            buyer_name=buyer_name,

            avatar_initial=(
                clean_optional_text(
                    avatar_initial
                )
            ),

            platform=platform,

            account_type_label=(
                clean_optional_text(
                    account_type_label
                )
            ),

            rating=rating,

            review_date_text=(
                clean_optional_text(
                    review_date_text
                )
            ),

            review_text=review_text,

            status=review_status,
        )

    except ValidationError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=jsonable_encoder(
                error.errors()
            ),
        ) from error

    saved_file_path: Path | None = None
    review_id: int | None = None

    try:
        review = crud.create_review(
            db=db,
            payload=payload,
        )

        review_id = review.id

        if screenshot is not None:
            screenshot_data = (
                await save_review_screenshot(
                    upload=screenshot,
                    review_id=review.id,
                )
            )

            saved_file_path = (
                screenshot_data.pop(
                    "absolute_path"
                )
            )

            review.screenshot_url = (
                screenshot_data[
                    "screenshot_url"
                ]
            )

            review.screenshot_file_name = (
                screenshot_data[
                    "screenshot_file_name"
                ]
            )

            review.screenshot_content_type = (
                screenshot_data[
                    "screenshot_content_type"
                ]
            )

            review.screenshot_size_bytes = (
                screenshot_data[
                    "screenshot_size_bytes"
                ]
            )

        db.commit()

    except HTTPException:
        db.rollback()

        if saved_file_path:
            saved_file_path.unlink(
                missing_ok=True
            )

        if review_id:
            shutil.rmtree(
                REVIEW_UPLOAD_ROOT /
                str(review_id),
                ignore_errors=True,
            )

        raise

    except IntegrityError as error:
        db.rollback()

        if saved_file_path:
            saved_file_path.unlink(
                missing_ok=True
            )

        if review_id:
            shutil.rmtree(
                REVIEW_UPLOAD_ROOT /
                str(review_id),
                ignore_errors=True,
            )

        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "Review could not be created "
                "because of a database conflict."
            ),
        ) from error

    except Exception:
        db.rollback()

        if review_id:
            shutil.rmtree(
                REVIEW_UPLOAD_ROOT /
                str(review_id),
                ignore_errors=True,
            )

        raise

    created_review = crud.get_review(
        db=db,
        review_id=review.id,
    )

    if created_review is None:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Review was created but "
                "could not be loaded."
            ),
        )

    return created_review


@router.get(
    "",
    response_model=PaginatedReviewResponse,
)
def get_all_reviews(
    page: int = Query(
        default=1,
        ge=1,
    ),

    page_size: int = Query(
        default=10,
        ge=1,
        le=100,
    ),

    review_status: ReviewStatus | None = Query(
        default=None,
        alias="status",
    ),

    db: Session = Depends(get_db),
):
    items, total = crud.get_reviews(
        db=db,
        page=page,
        page_size=page_size,
        status_filter=(
            review_status.value
            if review_status
            else None
        ),
    )

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get(
    "/{review_id}",
    response_model=ReviewResponse,
)
def get_review_by_id(
    review_id: int,
    db: Session = Depends(get_db),
):
    review = crud.get_review(
        db=db,
        review_id=review_id,
    )

    if review is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Review not found.",
        )

    return review


@router.patch(
    "/{review_id}",
    response_model=ReviewResponse,
)
def update_review_by_id(
    review_id: int,
    payload: ReviewUpdate,
    db: Session = Depends(get_db),
):
    review = crud.get_review(
        db=db,
        review_id=review_id,
    )

    if review is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Review not found.",
        )

    try:
        crud.update_review(
            db=db,
            review=review,
            payload=payload,
        )

        db.commit()

    except IntegrityError as error:
        db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "Review could not be updated."
            ),
        ) from error

    updated_review = crud.get_review(
        db=db,
        review_id=review_id,
    )

    if updated_review is None:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Review was updated but "
                "could not be loaded."
            ),
        )

    return updated_review


@router.delete(
    "/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_review_by_id(
    review_id: int,
    db: Session = Depends(get_db),
):
    review = crud.get_review(
        db=db,
        review_id=review_id,
    )

    if review is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Review not found.",
        )

    try:
        db.delete(review)
        db.commit()

    except IntegrityError as error:
        db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "Review could not be deleted."
            ),
        ) from error

    shutil.rmtree(
        REVIEW_UPLOAD_ROOT /
        str(review_id),
        ignore_errors=True,
    )

    return Response(
        status_code=(
            status.HTTP_204_NO_CONTENT
        )
    )