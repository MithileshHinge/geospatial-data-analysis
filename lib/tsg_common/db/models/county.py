from sqlalchemy import Column, String, Text, ForeignKey, Index

from .base_geo import BaseGeo


class County(BaseGeo):
    """County model representing US counties with geometry data."""

    __tablename__ = "counties"

    geoid = Column(String(5), primary_key=True, doc="5-digit county FIPS code")
    statefp = Column(
        String(2), ForeignKey("states.geoid"), nullable=False
    )  # Updated to match State model
    name = Column(Text, nullable=False)

    # Define spatial index for the geometry column
    __table_args__ = (Index("ix_counties_geom_gix", "geom", postgresql_using="gist"),)
