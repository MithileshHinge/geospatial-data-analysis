from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .settings import settings

_engine = create_engine(
    settings.get_db_url, pool_pre_ping=True, pool_size=5, max_overflow=10
)

SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)


def get_engine():
    return _engine
