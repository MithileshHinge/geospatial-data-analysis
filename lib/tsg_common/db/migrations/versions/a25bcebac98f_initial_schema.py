"""initial schema

Revision ID: a25bcebac98f
Revises: a0d357f04bc1
Create Date: 2025-05-06 09:04:22.921481

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

# revision identifiers, used by Alembic.
revision: str = "a25bcebac98f"
down_revision: Union[str, None] = "a0d357f04bc1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "msas",
        sa.Column("geoid", sa.String(length=5), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column(
            "geom",
            geoalchemy2.types.Geometry(
                geometry_type="MULTIPOLYGON",
                srid=4326,
                from_text="ST_GeomFromEWKT",
                name="geometry",
                nullable=False,
            ),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("geoid", name=op.f("pk_msas")),
    )
    op.create_index(
        "ix_msas_geom_gix", "msas", ["geom"], unique=False, postgresql_using="gist"
    )
    op.create_table(
        "quickfacts",
        sa.Column("layer", sa.Text(), nullable=False),
        sa.Column("geoid", sa.Text(), nullable=False),
        sa.Column("facts", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "updated", sa.Date(), server_default=sa.text("CURRENT_DATE"), nullable=False
        ),
        sa.PrimaryKeyConstraint("layer", "geoid", name=op.f("pk_quickfacts")),
    )
    op.create_table(
        "states",
        sa.Column("geoid", sa.String(length=2), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column(
            "geom",
            geoalchemy2.types.Geometry(
                geometry_type="MULTIPOLYGON",
                srid=4326,
                from_text="ST_GeomFromEWKT",
                name="geometry",
                nullable=False,
            ),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("geoid", name=op.f("pk_states")),
    )
    op.create_index(
        "ix_states_geom_gix", "states", ["geom"], unique=False, postgresql_using="gist"
    )
    op.create_table(
        "counties",
        sa.Column("geoid", sa.String(length=5), nullable=False),
        sa.Column("statefp", sa.String(length=2), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column(
            "geom",
            geoalchemy2.types.Geometry(
                geometry_type="MULTIPOLYGON",
                srid=4326,
                from_text="ST_GeomFromEWKT",
                name="geometry",
                nullable=False,
            ),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["statefp"],
            ["states.geoid"],
            name=op.f("fk_counties_counties_statefp_states"),
        ),
        sa.PrimaryKeyConstraint("geoid", name=op.f("pk_counties")),
    )
    op.create_index(
        "ix_counties_geom_gix",
        "counties",
        ["geom"],
        unique=False,
        postgresql_using="gist",
    )
    op.create_table(
        "places",
        sa.Column("geoid", sa.String(length=7), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("statefp", sa.String(length=2), nullable=False),
        sa.Column(
            "centroid",
            geoalchemy2.types.Geometry(
                geometry_type="POINT",
                srid=4326,
                from_text="ST_GeomFromEWKT",
                name="geometry",
            ),
            sa.Computed("ST_PointOnSurface(geom)", persisted=True),
            nullable=True,
        ),
        sa.Column(
            "geom",
            geoalchemy2.types.Geometry(
                geometry_type="MULTIPOLYGON",
                srid=4326,
                from_text="ST_GeomFromEWKT",
                name="geometry",
                nullable=False,
            ),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["statefp"], ["states.geoid"], name=op.f("fk_places_places_statefp_states")
        ),
        sa.PrimaryKeyConstraint("geoid", name=op.f("pk_places")),
    )

    op.create_index(
        "ix_places_centroid_geog_gix",
        "places",
        [sa.literal_column("(centroid::geography)")],
        unique=False,
        postgresql_using="gist",
    )
    op.create_index(
        "ix_places_centroid_gix",
        "places",
        ["centroid"],
        unique=False,
        postgresql_using="gist",
    )
    op.create_index(
        "ix_places_geom_gix", "places", ["geom"], unique=False, postgresql_using="gist"
    )

    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("ix_places_geom_gix", table_name="places", postgresql_using="gist")
    op.drop_index(
        "ix_places_centroid_gix", table_name="places", postgresql_using="gist"
    )
    op.drop_index(
        "ix_places_centroid_geog_gix", table_name="places", postgresql_using="gist"
    )
    op.drop_table("places")
    op.drop_index(
        "ix_counties_geom_gix", table_name="counties", postgresql_using="gist"
    )
    op.drop_table("counties")
    op.drop_index("ix_states_geom_gix", table_name="states", postgresql_using="gist")
    op.drop_table("states")
    op.drop_table("quickfacts")
    op.drop_index("ix_msas_geom_gix", table_name="msas", postgresql_using="gist")
    op.drop_table("msas")
    # ### end Alembic commands ###
