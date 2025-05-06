import geopandas as gpd
from pathlib import Path
from typing import Any, Dict, Iterable
import zipfile

from tsg_common.s3_utils import download_to_tempfile
from tsg_common.db import models

from settings import settings
from tiger_s3_paths import TigerS3Paths


shapefile_tmp = Path("/tmp/shp")
shapefile_tmp.mkdir(parents=True, exist_ok=True)


def _extract_shapefile_zip(zip_path: Path) -> Path:
    with zipfile.ZipFile(zip_path) as zf:
        shp_files = [m for m in zf.namelist() if m.endswith(".shp")]
        if not shp_files:
            raise RuntimeError(f"No .shp inside {zip_path}")
        zf.extractall(path=zip_path.parent)
        return zip_path.parent / shp_files[0]


def load_international_shapefile(shp_path: Path) -> Iterable[models.International]:
    gdf = gpd.read_file(shp_path)
    for rec in gdf.itertuples(index=False):
        row = rec._asdict()
        yield models.International(
            geoid=row["GEOID"],
            name=row["NAME"],
            geom=row["geometry"],
        )


def load_state_shapefile(
    shp_path: Path, wanted_geoids: set[str], name_map: Dict[str, str]
) -> Iterable[models.State]:
    gdf = gpd.read_file(shp_path)

    gdf = gdf[gdf["GEOID"].isin(wanted_geoids)]

    # override name with QuickFacts header if present
    gdf["NAME"] = gdf["GEOID"].map(name_map).fillna(gdf["NAME"])

    for rec in gdf.itertuples(index=False):
        row = rec._asdict()
        yield models.State(
            geoid=row["GEOID"],
            name=row["NAME"],
            geom=row["geometry"],
        )


def load_county_shapefile(
    shp_path: Path, wanted_geoids: set[str], name_map: Dict[str, str]
) -> Iterable[models.County]:
    gdf = gpd.read_file(shp_path)

    gdf = gdf[gdf["GEOID"].isin(wanted_geoids)]

    # override name with QuickFacts header if present
    gdf["NAME"] = gdf["GEOID"].map(name_map).fillna(gdf["NAME"])

    for rec in gdf.itertuples(index=False):
        row = rec._asdict()
        yield models.County(
            geoid=row["GEOID"],
            name=row["NAMELSAD"],
            statefp=row["STATEFP"],
            geom=row["geometry"],
        )


def load_place_shapefile(
    shp_path: Path, wanted_geoids: set[str], name_map: Dict[str, str]
) -> Iterable[models.Place]:
    gdf = gpd.read_file(shp_path)

    gdf = gdf[gdf["GEOID"].isin(wanted_geoids)]

    # override name with QuickFacts header if present
    gdf["NAME"] = gdf["GEOID"].map(name_map).fillna(gdf["NAME"])

    for rec in gdf.itertuples(index=False):
        row = rec._asdict()
        yield models.Place(
            geoid=row["GEOID"],
            name=row["NAMELSAD"],
            statefp=row["STATEFP"],
            geom=row["geometry"],
        )


def load_msa_shapefile(
    shp_path: Path, wanted_geoids: set[str] | None, name_map: Dict[str, str]
) -> Iterable[models.MSA]:
    gdf = gpd.read_file(shp_path)

    if wanted_geoids is not None:
        gdf = gdf[gdf["GEOID"].isin(wanted_geoids)]

    gdf["NAME"] = gdf["GEOID"].map(name_map).fillna(gdf["NAME"])

    for rec in gdf.itertuples(index=False):
        row = rec._asdict()
        yield models.MSA(
            geoid=row["GEOID"],
            name=row["NAME"],
            geom=row["geometry"],
        )


def clean_up_temp_files(zip_path: Path, shp_path: Path):
    zip_path.unlink()
    for p in shp_path.parent.iterdir():
        p.unlink()
    shp_path.parent.rmdir()


def extract_tiger_files(
    s3_client: Any,
    tiger_s3_paths: TigerS3Paths,
    geo_sets: Dict[str, set[str]],
    name_map: Dict[str, str],
):
    # Process international boundary
    international_zip = download_to_tempfile(
        s3_client, settings.s3_bucket, tiger_s3_paths.international
    )
    international_shp = _extract_shapefile_zip(international_zip)
    international_rows = list(load_international_shapefile(international_shp))
    clean_up_temp_files(international_zip, international_shp)

    # Process states
    state_zip = download_to_tempfile(
        s3_client, settings.s3_bucket, tiger_s3_paths.state
    )
    state_shp = _extract_shapefile_zip(state_zip)
    state_rows = list(load_state_shapefile(state_shp, geo_sets["states"], name_map))
    clean_up_temp_files(state_zip, state_shp)

    # Process counties
    county_zip = download_to_tempfile(
        s3_client, settings.s3_bucket, tiger_s3_paths.county
    )
    county_shp = _extract_shapefile_zip(county_zip)
    county_rows = list(
        load_county_shapefile(county_shp, geo_sets["counties"], name_map)
    )
    clean_up_temp_files(county_zip, county_shp)

    # Process MSAs
    msa_zip = download_to_tempfile(s3_client, settings.s3_bucket, tiger_s3_paths.cbsa)
    msa_shp = _extract_shapefile_zip(msa_zip)
    msa_rows = list(load_msa_shapefile(msa_shp, None, name_map))
    clean_up_temp_files(msa_zip, msa_shp)

    # Process places
    place_rows = []
    for place_path in tiger_s3_paths.places:
        place_zip = download_to_tempfile(s3_client, settings.s3_bucket, place_path)
        place_shp = _extract_shapefile_zip(place_zip)
        place_rows.extend(
            list(load_place_shapefile(place_shp, geo_sets["places"], name_map))
        )
        clean_up_temp_files(place_zip, place_shp)

    return international_rows, state_rows, county_rows, msa_rows, place_rows
