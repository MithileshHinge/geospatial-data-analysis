from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from typing import Iterable, Sequence, Type
from geoalchemy2.shape import from_shape

from .base import Base
from .models import International, State, County, MSA, Place, QuickFacts


class WriteQueries:
    """
    Thin wrappers around bulk-insert / upsert patterns so the ETL loader
    never writes raw SQL in the pipeline script.  All methods COMMIT.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def _bulk_upsert(
        self,
        table: Type[Base],
        rows: list[dict],
        pkey_cols: Sequence[str],
    ) -> None:
        """
        Core routine: bulk insert with ON CONFLICT DO UPDATE. Suitable
        for all static layer tables plus QuickFacts.
        """

        stmt = insert(table).values(rows)

        update_dict = {
            c.name: stmt.excluded[c.name]
            for c in table.__table__.columns
            if c.name not in pkey_cols
            and not (hasattr(c, "computed") and c.computed is not None)
            and c.server_default is None
            and c.server_onupdate is None
        }

        stmt = stmt.on_conflict_do_update(index_elements=pkey_cols, set_=update_dict)

        self.db.execute(stmt)
        self.db.commit()

    def upsert_international(self, rows: Iterable[International]) -> None:
        """
        Bulk insert or update International rows.
        """
        values = []
        for row in rows:
            row_dict = {
                "geoid": row.geoid,
                "name": row.name,
                "geom": from_shape(row.geom, srid=4326),
            }
            values.append(row_dict)

        self._bulk_upsert(International, values, ["geoid"])

    def upsert_states(self, rows: Iterable[State]) -> None:
        """
        Bulk insert or update State rows.
        """
        values = []
        for row in rows:
            row_dict = {
                "geoid": row.geoid,
                "name": row.name,
                "geom": from_shape(row.geom, srid=4326),
            }
            values.append(row_dict)

        self._bulk_upsert(State, values, ["geoid"])

    def upsert_counties(self, rows: Iterable[County]) -> None:
        """
        Bulk insert or update County rows.
        """
        values = []
        for row in rows:
            row_dict = {
                "geoid": row.geoid,
                "statefp": row.statefp,
                "name": row.name,
                "geom": from_shape(row.geom, srid=4326),
            }
            values.append(row_dict)
        self._bulk_upsert(County, values, ["geoid"])

    def upsert_msas(self, rows: Iterable[MSA]) -> None:
        """
        Bulk insert or update MSA rows.
        """
        values = []
        for row in rows:
            row_dict = {
                "geoid": row.geoid,
                "name": row.name,
                "geom": from_shape(row.geom, srid=4326),
            }
            values.append(row_dict)
        self._bulk_upsert(MSA, values, ["geoid"])

    def upsert_places(self, rows: Iterable[Place]) -> None:
        """
        Bulk insert or update Place rows.
        """
        values = []
        for row in rows:
            row_dict = {
                "geoid": row.geoid,
                "name": row.name,
                "statefp": row.statefp,
                "geom": from_shape(row.geom, srid=4326),
            }
            values.append(row_dict)
        self._bulk_upsert(Place, values, ["geoid"])

    def upsert_quickfacts(self, rows: Iterable[QuickFacts]) -> None:
        """
        Bulk insert or update QuickFacts rows.
        """
        values = []
        for row in rows:
            row_dict = {
                "layer": row.layer,
                "geoid": row.geoid,
                "facts": row.facts,
            }
            values.append(row_dict)

        self._bulk_upsert(QuickFacts, values, ["layer", "geoid"])
