from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        # Vercel (y otros paneles) a veces dejan una variable definida pero
        # vacía en vez de simplemente no crearla. Sin esto, pydantic trata ""
        # como un valor real -- int("") revienta con un ValidationError
        # críptico y tumba toda la app al importar app.main (ver BACKEND_PORT).
        # Con esto, "" se trata como "no definida": los campos con default
        # (BACKEND_PORT, JWT_EXPIRE_MINUTES, etc.) usan su default, y los
        # campos obligatorios (DATABASE_URL) fallan con un mensaje claro de
        # "field required" en vez de un error de parseo confuso.
        env_ignore_empty=True,
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

    # CU03 - Recuperar contraseña: SMTP estándar para enviar el correo real con
    # el enlace de restablecimiento (ver app/integrations/mailer.py). Vacíos
    # por defecto: sin MAIL_HOST/MAIL_FROM configurados, el envío falla de
    # forma explícita en vez de intentar conectarse a un servidor inexistente.
    MAIL_HOST: str = ""
    MAIL_PORT: int = 587
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = ""
    MAIL_USE_TLS: bool = True

    # Minutos de validez del token de CU03 antes de expirar.
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30

    # URL pública del frontend Angular. CU03 la usa para construir el enlace
    # de restablecimiento que se envía por correo -- nunca hardcodear
    # localhost: en producción se define vía variable de entorno. CU23
    # (procesar pago electrónico) reutiliza esta misma variable para armar
    # success_url/cancel_url de Stripe Checkout -- no se creó una
    # FRONTEND_BASE_URL aparte porque esta ya cumple exactamente ese rol.
    FRONTEND_URL: str = "http://localhost:4200"

    # CU23 - Procesar pago electrónico (Stripe Checkout Hosted, modo TEST).
    # Vacía por defecto: sin configurar, app/integrations/stripe_client.py
    # falla de forma explícita (mismo criterio que MAIL_HOST/CU03) en vez de
    # intentar llamar a Stripe con una clave inválida. NUNCA se expone a
    # Angular ni se imprime en logs -- ver stripe_client.py.
    STRIPE_SECRET_KEY: str = ""
    # Moneda de Checkout -- Bs (boliviano) es "bob", pero no toda cuenta de
    # Stripe TEST admite esa moneda para Checkout; si stripe_client.py
    # rechaza la sesión por moneda no soportada, cambiar esta variable (ej.
    # a "usd") sin tocar código.
    STRIPE_CURRENCY: str = "bob"

    # CU29 - Obtener recomendaciones mediante IA (Gemini API). Vacía por
    # defecto: sin configurar,
    # modules/P6_InnovacionYAnalisis/CU29_ObtenerRecomendacionesIA/gemini_client.py
    # falla de forma explícita (mismo criterio que STRIPE_SECRET_KEY/CU23) en
    # vez de intentar llamar a Gemini con una clave inválida -- el asistente
    # cae a su respuesta de fallback, el catálogo nunca se cae. NUNCA se
    # expone a Angular ni se imprime en logs.
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.7-flash"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
