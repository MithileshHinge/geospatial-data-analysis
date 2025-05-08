from collections import defaultdict
import logging
import sys
from typing import Dict

from tsg_common.s3_utils import get_s3_client, iter_objects, download_to_tempfile
from tsg_common.db import SessionLocal, WriteQueries
from tsg_common.db.models import QuickFacts

from extract_tiger_files import extract_tiger_files
from tiger_s3_paths import TigerS3Paths
from settings import settings
from parse_quickfacts import parse_quickfacts

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def main() -> None:
    s3_client = get_s3_client(
        region=settings.region,
        endpoint=settings.s3_endpoint,
    )

    # Collect and parse all QuickFacts CSV files
    name_map: Dict[str, str] = {}
    facts_rows: list[QuickFacts] = []
    geo_sets: defaultdict[str, set[str]] = defaultdict(set)

    quickfacts_prefix = f"{settings.s3_prefix}/quickfacts"
    for obj in iter_objects(s3_client, settings.s3_bucket, quickfacts_prefix):
        local_path = download_to_tempfile(s3_client, settings.s3_bucket, obj["Key"])
        nmap, f_rows, g_sets = parse_quickfacts(local_path)
        name_map.update(nmap)
        facts_rows.extend(f_rows)
        for layer, geoids in g_sets.items():
            geo_sets[layer].update(geoids)
        local_path.unlink()

    logger.info(
        "QuickFacts parsed: %d states, %d counties, %d places",
        len(geo_sets["states"]),
        len(geo_sets["counties"]),
        len(geo_sets["places"]),
    )

    # Download TIGER zips and feed to loader
    tiger_paths = TigerS3Paths.from_base_s3_path(s3_client, settings.s3_prefix)

    state_rows, county_rows, msa_rows, place_rows = extract_tiger_files(
        s3_client, tiger_paths, geo_sets, name_map
    )

    logger.info(
        "TIGER files extracted: %d states, %d counties, %d places, %d MSAs",
        len(state_rows),
        len(county_rows),
        len(place_rows),
        len(msa_rows),
    )
    logger.info("Writing to database")

    with SessionLocal() as db:
        wq = WriteQueries(db)
        wq.upsert_states(state_rows)
        logger.info("States written to database")
        wq.upsert_counties(county_rows)
        logger.info("Counties written to database")
        wq.upsert_places(place_rows)
        logger.info("Places written to database")
        wq.upsert_msas(msa_rows)
        logger.info("MSAs written to database")
        wq.upsert_quickfacts(facts_rows)
        logger.info("Quickfacts written to database")


if __name__ == "__main__":
    main()
