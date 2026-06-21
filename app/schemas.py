from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)
class ReviewStatus(str, Enum):
    published = "published"
    hidden = "hidden"


class Platform(str, Enum):
    instagram = "instagram"
    youtube = "youtube"
    tiktok = "tiktok"
    facebook = "facebook"
    x = "x"
    telegram = "telegram"
    linkedin = "linkedin"
    other = "other"


class PaymentMethod(str, Enum):
    paypal = "paypal"
    crypto = "crypto"


class ListingStatus(str, Enum):
    pending = "pending"
    under_review = "under_review"
    approved = "approved"
    rejected = "rejected"
    sold = "sold"


class ListingCreate(BaseModel):
    platform: Platform

    username: str | None = Field(
        default=None,
        max_length=255,
    )

    account_url: HttpUrl

    followers_count: int = Field(ge=0)

    reach_last_28_days: int | None = Field(
        default=None,
        ge=0,
    )

    reach_last_90_days: int | None = Field(
        default=None,
        ge=0,
    )

    account_age_months: int = Field(
        default=0,
        ge=0,
    )

    top_country: str | None = Field(
        default=None,
        max_length=150,
    )

    second_top_country: str | None = Field(
        default=None,
        max_length=150,
    )

    third_top_country: str | None = Field(
        default=None,
        max_length=150,
    )

    niche: str | None = Field(
        default=None,
        max_length=100,
    )

    is_monetized: bool = False

    average_monthly_revenue_usd: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=12,
        decimal_places=2,
    )

    audience_male_percentage: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
        max_digits=5,
        decimal_places=2,
    )

    audience_female_percentage: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
        max_digits=5,
        decimal_places=2,
    )

    account_created_date_text: str | None = Field(
        default=None,
        max_length=100,
    )

    has_original_email: bool = False

    is_price_negotiable: bool = False
    is_escrow_accepted: bool = False

    asking_price_usd: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=2,
    )

    original_price_usd: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=12,
        decimal_places=2,
    )

    is_promoted: bool = False
    is_flash_sale: bool = False

    payment_methods: list[PaymentMethod] = Field(
        default_factory=list,
    )

    @model_validator(mode="after")
    def validate_listing(self):
        if (
            self.is_monetized
            and self.average_monthly_revenue_usd is None
        ):
            raise ValueError(
                "Average monthly revenue is required "
                "for a monetized account."
            )

        if not self.is_monetized:
            self.average_monthly_revenue_usd = None

        male = self.audience_male_percentage
        female = self.audience_female_percentage

        if (
            male is not None
            and female is not None
            and male + female > 100
        ):
            raise ValueError(
                "Male and female audience total "
                "cannot be greater than 100."
            )

        if (
            self.is_flash_sale
            and self.original_price_usd is None
        ):
            raise ValueError(
                "Original price is required "
                "for a flash sale listing."
            )

        return self

class ListingUpdate(BaseModel):
    platform: Platform | None = None
    account_url: HttpUrl | None = None

    followers_count: int | None = Field(
        default=None,
        ge=0,
    )

    reach_last_28_days: int | None = Field(
        default=None,
        ge=0,
    )

    account_age_months: int | None = Field(
        default=None,
        ge=0,
    )

    top_country: str | None = Field(
        default=None,
        max_length=100,
    )

    is_monetized: bool | None = None

    average_monthly_revenue_usd: Decimal | None = Field(
        default=None,
        ge=0,
    )

    is_price_negotiable: bool | None = None
    is_escrow_accepted: bool | None = None

    asking_price_usd: Decimal | None = Field(
        default=None,
        gt=0,
    )

    status: ListingStatus | None = None
    admin_note: str | None = None

    payment_methods: list[PaymentMethod] | None = None
    username: str | None = Field(
    default=None,
    max_length=255,
)

reach_last_90_days: int | None = Field(
    default=None,
    ge=0,
)

second_top_country: str | None = Field(
    default=None,
    max_length=150,
)

third_top_country: str | None = Field(
    default=None,
    max_length=150,
)

niche: str | None = Field(
    default=None,
    max_length=100,
)

audience_male_percentage: Decimal | None = Field(
    default=None,
    ge=0,
    le=100,
)

audience_female_percentage: Decimal | None = Field(
    default=None,
    ge=0,
    le=100,
)

account_created_date_text: str | None = Field(
    default=None,
    max_length=100,
)

has_original_email: bool | None = None

original_price_usd: Decimal | None = Field(
    default=None,
    gt=0,
)

is_promoted: bool | None = None
is_flash_sale: bool | None = None

class PaymentMethodResponse(BaseModel):
    id: int
    payment_method: PaymentMethod

    @field_validator("payment_method", mode="before")
    @classmethod
    def normalize_payment_method(cls, v):
        if isinstance(v, str):
            normalized = v.lower().replace(" ", "_")
            # map legacy values
            aliases = {"bank_transfer": "crypto"}
            return aliases.get(normalized, normalized)
        return v

    model_config = ConfigDict(from_attributes=True)


class ScreenshotResponse(BaseModel):
    id: int
    original_filename: str
    file_url: str
    mime_type: str
    file_size_bytes: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ListingResponse(BaseModel):
    id: int

    platform: Platform
    username: str | None
    account_url: str

    followers_count: int
    reach_last_28_days: int | None
    reach_last_90_days: int | None
    account_age_months: int

    top_country: str | None
    second_top_country: str | None
    third_top_country: str | None
    niche: str | None

    is_monetized: bool
    average_monthly_revenue_usd: Decimal | None

    audience_male_percentage: Decimal | None
    audience_female_percentage: Decimal | None

    account_created_date_text: str | None
    has_original_email: bool

    is_price_negotiable: bool
    is_escrow_accepted: bool

    asking_price_usd: Decimal
    original_price_usd: Decimal | None

    is_promoted: bool
    is_flash_sale: bool

    status: ListingStatus
    admin_note: str | None

    created_at: datetime
    updated_at: datetime

    payment_methods: list[PaymentMethodResponse]
    screenshots: list[ScreenshotResponse]

    @field_validator("platform", mode="before")
    @classmethod
    def normalize_platform(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, v):
        if isinstance(v, str):
            normalized = v.lower()
            # map legacy DB values to current enum values
            aliases = {"active": "approved"}
            return aliases.get(normalized, normalized)
        return v

    model_config = ConfigDict(
        from_attributes=True
    )

class PaginatedListingResponse(BaseModel):
    items: list[ListingResponse]
    total: int
    page: int
    page_size: int
    

class ReviewCreate(BaseModel):
    buyer_name: str = Field(
        min_length=2,
        max_length=150,
    )

    avatar_initial: str | None = Field(
        default=None,
        max_length=3,
    )

    platform: Platform

    account_type_label: str | None = Field(
        default=None,
        max_length=150,
    )

    rating: int = Field(
        ge=1,
        le=5,
    )

    review_date_text: str | None = Field(
        default=None,
        max_length=50,
    )

    review_text: str = Field(
        min_length=3,
        max_length=5000,
    )

    status: ReviewStatus = (
        ReviewStatus.published
    )

    @field_validator(
        "buyer_name",
        "avatar_initial",
        "account_type_label",
        "review_date_text",
        "review_text",
        mode="before",
    )
    @classmethod
    def clean_text_fields(cls, value):
        if value is None:
            return None

        cleaned_value = str(value).strip()

        return cleaned_value or None

    @field_validator("avatar_initial")
    @classmethod
    def normalize_avatar_initial(
        cls,
        value: str | None,
    ):
        if value is None:
            return None

        return value.upper()
    
    
class ReviewUpdate(BaseModel):
    buyer_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    avatar_initial: str | None = Field(
        default=None,
        max_length=3,
    )

    platform: Platform | None = None

    account_type_label: str | None = Field(
        default=None,
        max_length=150,
    )

    rating: int | None = Field(
        default=None,
        ge=1,
        le=5,
    )

    review_date_text: str | None = Field(
        default=None,
        max_length=50,
    )

    review_text: str | None = Field(
        default=None,
        min_length=3,
        max_length=5000,
    )

    status: ReviewStatus | None = None
    
class ReviewResponse(BaseModel):
    id: int

    buyer_name: str
    avatar_initial: str | None

    platform: Platform
    account_type_label: str | None

    rating: int
    review_date_text: str | None
    review_text: str

    screenshot_url: str | None
    screenshot_file_name: str | None
    screenshot_content_type: str | None
    screenshot_size_bytes: int | None

    status: ReviewStatus

    created_at: datetime
    updated_at: datetime

    @field_validator("platform", mode="before")
    @classmethod
    def normalize_platform(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v

    model_config = ConfigDict(
        from_attributes=True
    )

class PaginatedReviewResponse(BaseModel):
    items: list[ReviewResponse]
    total: int
    page: int
    page_size: int