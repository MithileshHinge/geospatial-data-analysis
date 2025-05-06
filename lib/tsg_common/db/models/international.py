from sqlalchemy import Column, String, Text

from .base_geo import BaseGeo


class International(BaseGeo):
    """International boundary geometry model."""

    __tablename__ = "international"

    geoid = Column(
        String(2), primary_key=True, doc="Static 00 code, only single country"
    )
    name = Column(Text, nullable=False)
