import os
from typing import Any

from models.tiger_paths import TigerPaths
from utils import batch_download_files_to_s3, get_httpx_client


TIGER_BASE_URL = "https://www2.census.gov/geo/tiger"


async def download_tiger_files(s3: Any, dest_prefix: str) -> TigerPaths:
    async with get_httpx_client() as client:
        latest_tiger_year = "2024"  # TODO: Make this dynamic
        tiger_dl_urls = await TigerPaths.from_base_url(
            client, TIGER_BASE_URL, latest_tiger_year
        )

        urls_in_order = [
            tiger_dl_urls.international,
            tiger_dl_urls.state,
            tiger_dl_urls.county,
            tiger_dl_urls.cbsa,
            *tiger_dl_urls.places,
        ]
        results = await batch_download_files_to_s3(
            client,
            s3,
            urls_to_dest_path={
                url: os.path.join(dest_prefix, url[len(TIGER_BASE_URL) :].lstrip("/"))
                for url in urls_in_order
            },
        )

    (
        international_s3_path,
        state_s3_path,
        county_s3_path,
        cbsa_s3_path,
        *place_s3_paths,
    ) = results

    # Create and return TigerPaths with S3 paths
    return TigerPaths(
        international=international_s3_path,
        state=state_s3_path,
        county=county_s3_path,
        cbsa=cbsa_s3_path,
        places=place_s3_paths,
    )
