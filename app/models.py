from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class SocialAccountListing(Base):
    __tablename__ = "social_account_listings"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    platform: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    username: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    account_url: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    followers_count: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    reach_last_28_days: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    reach_last_90_days: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    account_age_months: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
        server_default=text("0"),
    )

    top_country: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    second_top_country: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    third_top_country: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    niche: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    is_monetized: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )

    average_monthly_revenue_usd: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    audience_male_percentage: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    audience_female_percentage: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    account_created_date_text: Mapped[
        str | None
    ] = mapped_column(
        String(100),
        nullable=True,
    )

    has_original_email: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )

    is_selling: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("0"),
    )

    is_price_negotiable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )

    is_escrow_accepted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )

    asking_price_usd: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    original_price_usd: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    is_promoted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )

    is_flash_sale: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default=text("'pending'"),
        index=True,
    )

    admin_note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=datetime.utcnow,
    )

    payment_methods: Mapped[
        list["ListingPaymentMethod"]
    ] = relationship(
        back_populates="listing",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    screenshots: Mapped[
        list["ListingScreenshot"]
    ] = relationship(
        back_populates="listing",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )
reach_last_90_days: Mapped[int | None] = mapped_column(
    BigInteger,
    nullable=True,
)

second_top_country: Mapped[str | None] = mapped_column(
    String(150),
    nullable=True,
)

third_top_country: Mapped[str | None] = mapped_column(
    String(150),
    nullable=True,
)

niche: Mapped[str | None] = mapped_column(
    String(100),
    nullable=True,
)

audience_male_percentage: Mapped[
    Decimal | None
] = mapped_column(
    Numeric(5, 2),
    nullable=True,
)

audience_female_percentage: Mapped[
    Decimal | None
] = mapped_column(
    Numeric(5, 2),
    nullable=True,
)

account_created_date_text: Mapped[
    str | None
] = mapped_column(
    String(100),
    nullable=True,
)

has_original_email: Mapped[bool] = mapped_column(
    Boolean,
    nullable=False,
    default=False,
    server_default=text("0"),
)

original_price_usd: Mapped[
    Decimal | None
] = mapped_column(
    Numeric(12, 2),
    nullable=True,
)

is_promoted: Mapped[bool] = mapped_column(
    Boolean,
    nullable=False,
    default=False,
    server_default=text("0"),
)

is_flash_sale: Mapped[bool] = mapped_column(
    Boolean,
    nullable=False,
    default=False,
    server_default=text("0"),
)


class ListingPaymentMethod(Base):
    __tablename__ = "listing_payment_methods"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    listing_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "social_account_listings.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    payment_method: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    listing: Mapped["SocialAccountListing"] = relationship(
        back_populates="payment_methods",
    )


class ListingScreenshot(Base):
    __tablename__ = "listing_screenshots"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    listing_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "social_account_listings.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    stored_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    file_url: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    file_size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    listing: Mapped["SocialAccountListing"] = relationship(
        back_populates="screenshots",
    )
    
class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    buyer_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    avatar_initial: Mapped[str | None] = mapped_column(
        String(3),
        nullable=True,
    )

    platform: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    account_type_label: Mapped[
        str | None
    ] = mapped_column(
        String(150),
        nullable=True,
    )

    rating: Mapped[int] = mapped_column(
        nullable=False,
    )

    review_date_text: Mapped[
        str | None
    ] = mapped_column(
        String(50),
        nullable=True,
    )

    review_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    screenshot_url: Mapped[
        str | None
    ] = mapped_column(
        String(1000),
        nullable=True,
    )

    screenshot_file_name: Mapped[
        str | None
    ] = mapped_column(
        String(255),
        nullable=True,
    )

    screenshot_content_type: Mapped[
        str | None
    ] = mapped_column(
        String(100),
        nullable=True,
    )

    screenshot_size_bytes: Mapped[
        int | None
    ] = mapped_column(
        BigInteger,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="published",
        server_default=text("'published'"),
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
    )  
    