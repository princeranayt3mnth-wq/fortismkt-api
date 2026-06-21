from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError


UPLOAD_ROOT = Path("uploads/listings")

MAX_FILE_SIZE = 5 * 1024 * 1024

ALLOWED_FORMATS = {
    "JPEG": {
        "extension": ".jpg",
        "mime_type": "image/jpeg",
    },
    "PNG": {
        "extension": ".png",
        "mime_type": "image/png",
    },
}

REVIEW_UPLOAD_ROOT = Path(
    "uploads/reviews"
)

REVIEW_UPLOAD_ROOT.mkdir(
    parents=True,
    exist_ok=True,
)

MAX_REVIEW_SCREENSHOT_SIZE = (
    5 * 1024 * 1024
)

ALLOWED_REVIEW_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
}


async def save_listing_screenshot(
    upload: UploadFile,
    listing_id: int,
) -> dict:
    file_content = await upload.read()

    if not file_content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded screenshot is empty.",
        )

    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Each screenshot must be 5 MB or smaller.",
        )

    try:
        with Image.open(BytesIO(file_content)) as image:
            image_format = (image.format or "").upper()
            image.verify()

    except (UnidentifiedImageError, OSError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only valid PNG and JPG images are allowed.",
        )

    image_settings = ALLOWED_FORMATS.get(
        image_format
    )

    if image_settings is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only PNG and JPG images are allowed.",
        )

    listing_folder = UPLOAD_ROOT / str(listing_id)

    listing_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    stored_filename = (
        f"{uuid4().hex}"
        f"{image_settings['extension']}"
    )

    destination = listing_folder / stored_filename

    destination.write_bytes(file_content)

    safe_original_name = Path(
        upload.filename or "screenshot"
    ).name[:255]

    return {
        "original_filename": safe_original_name,
        "stored_filename": stored_filename,
        "file_url": (
            f"/uploads/listings/"
            f"{listing_id}/"
            f"{stored_filename}"
        ),
        "mime_type": image_settings["mime_type"],
        "file_size_bytes": len(file_content),
        "absolute_path": destination,
    }
    
    
async def save_review_screenshot(
    upload: UploadFile,
    review_id: int,
) -> dict:
    if not upload.filename:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail="Screenshot filename is missing.",
        )

    content_type = (
        upload.content_type or ""
    ).lower()

    extension = (
        ALLOWED_REVIEW_IMAGE_TYPES.get(
            content_type
        )
    )

    if extension is None:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=(
                "Only PNG and JPG screenshots "
                "are allowed."
            ),
        )

    file_content = await upload.read()

    if not file_content:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail="Screenshot file is empty.",
        )

    if (
        len(file_content) >
        MAX_REVIEW_SCREENSHOT_SIZE
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=(
                "Screenshot must be 5 MB "
                "or smaller."
            ),
        )

    review_directory = (
        REVIEW_UPLOAD_ROOT /
        str(review_id)
    )

    review_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    stored_file_name = (
        f"{uuid4().hex}{extension}"
    )

    absolute_path = (
        review_directory /
        stored_file_name
    )

    absolute_path.write_bytes(
        file_content
    )

    return {
        "screenshot_url": (
            f"/uploads/reviews/"
            f"{review_id}/"
            f"{stored_file_name}"
        ),
        "screenshot_file_name": (
            upload.filename
        ),
        "screenshot_content_type": (
            content_type
        ),
        "screenshot_size_bytes": (
            len(file_content)
        ),
        "absolute_path": absolute_path,
    }