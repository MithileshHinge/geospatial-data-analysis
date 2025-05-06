"""
Declarative base class and naming convention for all tables & constraints.
"""

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

metadata = MetaData(
    naming_convention={
        "pk": "pk_%(table_name)s",
        "ix": "ix_%(table_name)s_%(column_0_N_label)s",
        "uq": "uq_%(table_name)s_%(column_0_N_label)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_N_label)s_%(referred_table_name)s",
    }
)


class Base(DeclarativeBase):
    metadata = metadata
