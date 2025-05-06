from sqlalchemy import Column, String, Text, Index

from .base_geo import BaseGeo


class State(BaseGeo):
    """State model representing US states with geometry data."""

    __tablename__ = "states"

    geoid = Column(String(2), primary_key=True, doc="2-digit state FIPS code")
    name = Column(Text, nullable=False)

    # Define spatial index for the geometry column
    __table_args__ = (Index("ix_states_geom_gix", "geom", postgresql_using="gist"),)
