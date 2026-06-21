from sqlalchemy import text

from app.database import engine, SessionLocal
from app.models import SocialAccountListing, ListingPaymentMethod, ListingScreenshot, Review


def test_connection() -> None:
    with engine.connect() as conn:
        version = conn.scalar(text("SELECT version()"))
        db_name = conn.scalar(text("SELECT current_database()"))
        print("PostgreSQL connection successful")
        print("Version:", version)
        print("Database:", db_name)


def insert_sample_data() -> None:
    db = SessionLocal()
    try:
        # Insert a sample listing
        listing = SocialAccountListing(
            platform="Instagram",
            username="test_account",
            account_url="https://instagram.com/test_account",
            followers_count=50000,
            reach_last_28_days=120000,
            reach_last_90_days=350000,
            account_age_months=24,
            top_country="United States",
            second_top_country="United Kingdom",
            third_top_country="Canada",
            niche="Fitness",
            is_monetized=True,
            average_monthly_revenue_usd=500.00,
            audience_male_percentage=45.00,
            audience_female_percentage=55.00,
            account_created_date_text="Jan 2022",
            has_original_email=True,
            is_price_negotiable=True,
            is_escrow_accepted=True,
            asking_price_usd=2500.00,
            original_price_usd=3000.00,
            is_promoted=False,
            is_flash_sale=False,
            status="active",
        )
        db.add(listing)
        db.flush()  # get listing.id before commit

        # Insert payment methods
        for method in ["PayPal", "Crypto", "Bank Transfer"]:
            db.add(ListingPaymentMethod(listing_id=listing.id, payment_method=method))

        # Insert a sample review
        review = Review(
            buyer_name="John Doe",
            avatar_initial="JD",
            platform="Instagram",
            account_type_label="Fitness Account",
            rating=5,
            review_date_text="June 2025",
            review_text="Great seller, smooth transaction. Account was exactly as described!",
            status="published",
        )
        db.add(review)
        db.commit()

        print(f"\nSample listing inserted with ID: {listing.id}")
        print(f"Payment methods added: PayPal, Crypto, Bank Transfer")
        print(f"Sample review inserted")

        # Read back to verify
        fetched = db.get(SocialAccountListing, listing.id)
        print(f"\nVerification - Fetched listing: {fetched.platform} | @{fetched.username} | ${fetched.asking_price_usd}")
        print(f"Payment methods: {[p.payment_method for p in fetched.payment_methods]}")

        reviews = db.query(Review).all()
        print(f"Total reviews in DB: {len(reviews)}")

    except Exception as e:
        db.rollback()
        print("Error:", e)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    test_connection()
    insert_sample_data()
