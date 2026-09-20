from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    # prepare_threshold=None desactiva las prepared statements del lado del
    # servidor en psycopg3 (activas por defecto a partir del 5° execute de
    # una misma consulta). DATABASE_URL apunta al endpoint "pooler" de Neon
    # (PgBouncer en modo transacción): ese pooler puede servir cada
    # sentencia de una misma "sesión" lógica desde un backend de Postgres
    # físico distinto, y una prepared statement queda atada a un backend
    # específico -- bajo carga sostenida (muchas ejecuciones repetidas de la
    # misma forma de consulta, como los SELECT ... FOR UPDATE OF de
    # P4_ReservasYAtencion) esto produce fallos intermitentes y no
    # deterministas (p. ej. Postgres devolviendo un plan/columna de una
    # sentencia preparada distinta de la que realmente se envió). Neon
    # documenta este mismo problema para su pooler -- ver
    # https://neon.tech/docs/connect/connection-pooling#how-to-disable-prepared-statements.
    connect_args={"connect_timeout": 5, "prepare_threshold": None},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session and ensures it is closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
