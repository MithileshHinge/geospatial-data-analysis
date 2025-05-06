import logging
from typing import Any
import os

from validate_quickfacts import clean_quickfacts_csv, validate_quickfacts_csv
from models.geo_info import GeoInfo
from utils import (
    batch_download_files_to_s3,
    get_httpx_client,
    load_csv_file_from_s3,
    write_csv_file_to_s3,
)


QUICKFACTS_BASE_URL = "https://www.census.gov/quickfacts/fact/csv"


def _get_quickfacts_url(slugs: list[str]):
    """Get the Quickfacts URL for the given slugs."""
    if len(slugs) > 6:
        raise ValueError("Only up to 6 geographies are supported at a time.")
    return f"{QUICKFACTS_BASE_URL}/{','.join(slug for slug in slugs)}"


async def download_quickfacts(
    s3: Any, geo_infos: list[GeoInfo], dest_path: str
) -> list[str]:
    """
    Download the QuickFacts CSV files in batches of 6, because the QuickFacts website only allows 6 geographies at a time in the table.
    One CSV file is created for each batch.
    The CSV file name is the geoids of the geographies in the batch joined by a dash.

    Args:
        s3 (boto3.client): The S3 client.
        geo_infos (list[GeoInfo]): A list of GeoInfo objects.
        dest_path (str): The destination path.

    Returns:
        A list of downloaded CSV file paths (s3 keys).
    """

    # Group the geo_infos into batches of 6
    batches: list[list[GeoInfo]] = []
    for i in range(0, len(geo_infos), 6):
        geo_info_batch = geo_infos[i : i + 6]
        batches.append(geo_info_batch)

    urls_to_dest_path: dict[str, str] = {}
    dest_path_to_batch: dict[str, list[GeoInfo]] = {}
    for batch in batches:
        url = _get_quickfacts_url([geo_info.id for geo_info in batch])
        dest_file_path = os.path.join(
            dest_path, "-".join([geo_info.geoid for geo_info in batch]) + ".csv"
        )
        urls_to_dest_path[url] = dest_file_path
        dest_path_to_batch[dest_file_path] = batch

    async with get_httpx_client() as client:
        # Download all CSV files
        downloaded_paths = await batch_download_files_to_s3(
            client,
            s3,
            urls_to_dest_path,
        )

    for dest_file_path, batch in dest_path_to_batch.items():
        csv_content = load_csv_file_from_s3(s3, dest_file_path)
        cleaned_csv_content = clean_quickfacts_csv(csv_content)
        write_csv_file_to_s3(s3, dest_file_path, cleaned_csv_content)
        missing_geo_infos, missing_fips_codes = validate_quickfacts_csv(
            cleaned_csv_content, batch
        )

        if missing_geo_infos:
            logging.warning(
                "Missing geographies: %s  from file: %s",
                ", ".join([geo_info.label for geo_info in missing_geo_infos]),
                dest_file_path,
            )
        if missing_fips_codes:
            logging.warning(
                "Missing FIPS codes: %s  from file: %s",
                ", ".join(missing_fips_codes),
                dest_file_path,
            )

    return downloaded_paths
