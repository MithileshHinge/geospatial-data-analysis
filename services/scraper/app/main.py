#! /usr/bin/env python3

import asyncio
import logging
import sys
import os

from settings import settings
from scrape_search import scrape_search_results
from tiger_dl import download_tiger_files
from quickfacts_dl import download_quickfacts
from tsg_common.s3_utils import get_s3_client


async def main():
    s3 = get_s3_client(
        region=settings.region,
        endpoint=settings.s3_endpoint,
    )
    dest_prefix = "test"

    tiger_s3_paths = await download_tiger_files(s3, dest_prefix)
    logging.info("Downloaded TIGER files to s3")

    geo_infos, not_found = await scrape_search_results(tiger_s3_paths, s3, dest_prefix)
    logging.info(
        "Scraped search results from Quickfacts, found %d, missing %d",
        len(geo_infos),
        len(not_found),
    )

    await download_quickfacts(s3, geo_infos, os.path.join(dest_prefix, "quickfacts"))
    logging.info("Downloaded Quickfacts to s3")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    asyncio.run(main())
