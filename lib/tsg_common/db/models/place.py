from sqlalchemy import Column, String, Text, Computed, Index, ForeignKey
from geoalchemy2 import Geometry
from sqlalchemy.sql import text

from .base_geo import BaseGeo


class Place(BaseGeo):
    """Place model representing cities and towns."""

    __tablename__ = "places"

    geoid = Column(String(7), primary_key=True, doc="7-digit place FIPS code")
    name = Column(Text, nullable=False)
    statefp = Column(String(2), ForeignKey("states.geoid"), nullable=False)

    # Centroid is auto-generated column for point-radius searches
    centroid = Column(
        Geometry("POINT", srid=4326),
        Computed("ST_PointOnSurface(geom)", persisted=True),
    )

    # Define all indexes for the Place model
    __table_args__ = (
        # spatial index for the geometry column
        Index("ix_places_geom_gix", "geom", postgresql_using="gist"),
        # spatial index on centroid for fast point-radius search
        Index("ix_places_centroid_gix", "centroid", postgresql_using="gist"),
        # functional geography index to avoid run-time casts in distance calculations
        Index(
            "ix_places_centroid_geog_gix",
            text("(centroid::geography)"),
            postgresql_using="gist",
        ),
    )
