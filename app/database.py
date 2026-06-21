from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# Render provides "postgres://" but SQLAlchemy requires "postgresql+psycopg://"
_url = settings.database_url.replace(
    "postgres://", "postgresql+psycopg://", 1
).replace(
    "postgresql://", "postgresql+psycopg://", 1
)

engine = create_engine(
    _url,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
