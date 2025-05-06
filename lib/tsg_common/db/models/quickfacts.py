from sqlalchemy import Column, Text, Date
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from ..base import Base


class QuickFacts(Base):
    """QuickFacts model storing Census fact records for different geographic entities."""

    __tablename__ = "quickfacts"

    # Primary key on layer and geoid
    layer = Column(
        Text, primary_key=True, doc="Type of region (states/counties/places)"
    )
    geoid = Column(Text, primary_key=True, doc="Region identifier")
    facts = Column(JSONB, nullable=False, doc="Census fact record")
    updated = Column(
        Date,
        nullable=False,
        server_default=func.current_date(),
        onupdate=func.current_date(),
    )
