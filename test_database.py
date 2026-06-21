from sqlalchemy import text

from app.database import engine


def test_database() -> None:
    try:
        with engine.connect() as connection:
            mysql_version = connection.scalar(
                text("SELECT VERSION()")
            )

            database_name = connection.scalar(
                text("SELECT DATABASE()")
            )

            print("MySQL connection successful")
            print("Version:", mysql_version)
            print("Database:", database_name)

    except Exception as error:
        print("MySQL connection failed")
        print(error)


if __name__ == "__main__":
    test_database()