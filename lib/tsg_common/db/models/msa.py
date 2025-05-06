from sqlalchemy import Column, String, Text, Index

from .base_geo import BaseGeo


class MSA(BaseGeo):
    """Metropolitan Statistical Area model."""

    __tablename__ = "msas"

    geoid = Column(String(5), primary_key=True, doc="5-digit CBSA code")
    name = Column(Text, nullable=False)

    # Define spatial index for the geometry column
    __table_args__ = (Index("ix_msas_geom_gix", "geom", postgresql_using="gist"),)
