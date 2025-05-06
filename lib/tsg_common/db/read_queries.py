from sqlalchemy import (
    select,
    func,
    Select,
    text,
    true,
)
from sqlalchemy.orm import Session
from typing import Sequence
from geoalchemy2 import functions as gf
from geoalchemy2.types import Geography
from sqlalchemy.engine import RowMapping

from .models import Place, County, MSA, QuickFacts, State


class ReadQueries:
    """All DB reads exposed to the HTTP layer."""

    def __init__(self, db: Session):
        self.db = db

    def nearby_places(
        self, lat: float, lon: float, radius_km: int = 50, limit: int = 25
    ) -> Sequence[RowMapping]:
        """
        Return `limit` places whose centroid is within `radius_km`.
        Distance is returned in *kilometres* for direct JSON serialise.
        """
        pt_geog = gf.ST_SetSRID(gf.ST_MakePoint(lon, lat), 4326).cast(Geography)

        q = (
            select(
                Place.geoid.label("geoid"),
                Place.name.label("name"),
                (
                    func.ST_Distance(Place.centroid.cast(Geography), pt_geog) / 1000.0
                ).label("distance_km"),
                func.ST_Y(Place.centroid).label("lat"),
                func.ST_X(Place.centroid).label("lon"),
            )
            .where(
                gf.ST_DWithin(
                    Place.centroid.cast(Geography),
                    pt_geog,
                    radius_km * 1000,
                )
            )
            .order_by("distance_km")
            .limit(limit)
        )

        return self.db.execute(q).mappings().all()

    def reverse_lookup(
        self, lat: float, lon: float, layers: tuple[str, ...] = ("counties", "msas")
    ) -> dict:
        """
        Return the county and/or MSA whose polygon contains the point.
        Omits keys not requested in `layers`.
        """

        pt = gf.ST_SetSRID(gf.ST_MakePoint(lon, lat), 4326)

        out: dict = {}
        if "counties" in layers:
            county = self.db.scalar(
                select(County).where(gf.ST_Contains(County.geom, pt)).limit(1)
            )
            out["county"] = county

        if "msas" in layers:
            msa = self.db.scalar(
                select(MSA).where(gf.ST_Contains(MSA.geom, pt)).limit(1)
            )
            out["msa"] = msa

        return out

    def get_quickfacts(self, layer: str, geoid: str) -> dict | None:
        """
        Fetch the JSONB QuickFacts blob for any layer/geoid pair.
        """
        stmt = (
            select(QuickFacts.facts)
            .select_from(QuickFacts)
            .where(QuickFacts.layer == layer, QuickFacts.geoid == geoid)
            .limit(1)
        )
        res = self.db.scalar(stmt)
        return res

    def tile_data(
        self, layer: str, z: int, x: int, y: int, format: str = "mvt"
    ) -> bytes | str | None:
        """
        Returns a Mapbox vector tile (bytes) when fmt='mvt', or GeoJSON str.
        """

        MODEL = {
            "states": State,
            "counties": County,
            "msas": MSA,
            "places": Place,
        }[layer].__table__

        # 1️⃣  bbox of the tile in WGS-84
        bbox_cte = select(
            func.ST_Transform(
                func.ST_TileEnvelope(z, x, y),
                4326,
            ).label("geom_4326")
        ).cte("bbox")

        # 2️⃣  per-row geometry clipped & simplified for MVT
        mvt_rows_cte = (
            select(
                MODEL.c.geoid,
                MODEL.c.name,
                func.ST_AsMVTGeom(
                    MODEL.c.geom,
                    bbox_cte.c.geom_4326,
                    4096,  # extent
                    256,  # buffer
                    True,  # clip
                ).label("geom"),
            )
            .select_from(MODEL.join(bbox_cte, true()))  # cross-join bbox
            .where(MODEL.c.geom.op("&&")(bbox_cte.c.geom_4326))
        ).cte("mvt_rows")

        # 3️⃣  choose output format
        if format == "mvt":
            # ST_AsMVT needs a result-set and we add FROM mvt_rows
            mvt_stmt: Select = select(
                func.ST_AsMVT(
                    text("mvt_rows.*"),  # row-set Arg1
                    "layer",
                    4096,
                    "geom",
                )
            ).select_from(mvt_rows_cte)
            result = self.db.scalar(mvt_stmt)
            return None if result is None else bytes(result)

        else:  # fmt == "geojson" — handy for visual debugging
            gj_stmt: Select = select(
                func.ST_AsGeoJSON(func.ST_Collect(mvt_rows_cte.c.geom))
            )
            return self.db.scalar(gj_stmt)

    def health_check(self) -> bool:
        """
        Check if the database connection is healthy.
        """
        return self.db.execute(text("SELECT 1")).scalar() == 1
