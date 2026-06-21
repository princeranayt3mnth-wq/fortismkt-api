from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers.listings import router as listings_router
from fastapi.staticfiles import StaticFiles
from app.routers import (
    listings,
    reviews,
)

uploads_directory = Path("uploads")

uploads_directory.mkdir(
    parents=True,
    exist_ok=True,
)


app = FastAPI(
    title="FORTISMKT API",
    version="1.0.0",
    description=(
        "Backend API for social media account listings."
    ),
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://fortismarketplace.com",
        "http://localhost:5500",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        settings.frontend_origin,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads",
)


app.include_router(
    listings.router,
    prefix="/api/v1",
)

app.include_router(
    reviews.router,
    prefix="/api/v1",
)

@app.get("/")
def root():
    return {
        "success": True,
        "message": "FORTISMKT API is running.",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
    }