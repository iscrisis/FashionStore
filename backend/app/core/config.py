from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "FashionStore API"
    APP_ENV: str = "development"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str

    BACKEND_PORT: int = 8000

    # Comma-separated list of allowed origins, e.g. "http://localhost:4200,https://app.example.com"
    CORS_ORIGINS: str = ""

    # CU01 - Iniciar sesión (modules/P2_UsuariosYAccesos)
    JWT_SECRET_KEY: str = "dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24

    # Usado únicamente por scripts/seed_admin.py para crear el Administrador inicial.
    ADMIN_INITIAL_NAME: str = "Administrador FashionStore"
    ADMIN_INITIAL_EMAIL: str = "admin@fashionstore.com"
    ADMIN_INITIAL_PASSWORD: str = "changeme"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
