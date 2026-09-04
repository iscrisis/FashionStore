from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import health

app = FastAPI(
    title=settings.APP_NAME,
    description="API REST central de FashionStore. Consumida por el frontend web (Angular) "
    "y, en una etapa posterior, por la aplicación móvil (Flutter).",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["root"])
def root() -> dict:
    return {
        "name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "docs": "/docs",
    }
