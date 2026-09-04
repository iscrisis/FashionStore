from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base class for all SQLAlchemy models.

    Future model modules must import this Base and be imported from
    alembic/env.py so their metadata is picked up by autogenerate.
    """
