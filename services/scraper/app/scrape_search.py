import asyncio
import json
import logging
from typing import Any
import httpx
from urllib.parse import quote
import os

from utils import fetch_with_retries, get_httpx_client, load_dbf_file_from_s3
from models.tiger_paths import TigerPaths
from settings import settings
from models.geo_info import GeoInfo
from models.search_queries import (
    SearchQuery,
    StateSearchQuery,
    CountySearchQuery,
    PlaceSearchQuery,
)


QUICKFACTS_SEARCH_URL = "https://www.census.gov/quickfacts/search/json"
_semaphore = asyncio.BoundedSemaphore(settings.scrape_search_concurrency)


async def _get_search_results(
    client: httpx.AsyncClient, search_query_str: str
) -> list[GeoInfo]:
    """
    Get the search results on QuickFacts website for the given search query string.
    Returns a list of GeoInfo objects.
    """
    url = f"{QUICKFACTS_SEARCH_URL}?type=geo&search={quote(search_query_str)}"
    response = await fetch_with_retries(client, url)
    response_json = json.loads(response.decode("utf-8"))
    if response_json["data"]:
        if (
            len(response_json["data"]) == 1
            and response_json["data"][0]["geoid"] is None
        ):
            return []
        else:
            # Have to strip() because some labels have trailing whitespaces
            # (e.g. "Kailua CDP (Honolulu County), Hawaii\n", "El Sobrante CDP (Contra Costa County), California\r")
            return [
                GeoInfo(
                    geoid=result["geoid"].strip(),
                    id=result["id"].strip(),
                    label=result["label"].strip(),
                    level=result["level"].strip(),
                )
                for result in response_json["data"]
            ]
    else:
        raise Exception(f"Unexpected response from QuickFacts: {response_json}")


async def _scrape_search_for_queries(
    search_queries: list[SearchQuery],
) -> tuple[list[GeoInfo], list[str]]:
    """
    Scrape QuickFacts search results for the given search queries.

    Args:
        search_queries (list[SearchQuery]): A list of search queries.

    Returns:
        list[GeoInfo]: A list of scraped GeoInfo objects.
        list[str]: A list of GEOIDs that could not be found.
    """
    geo_infos: dict[str, GeoInfo] = {}
    not_found: list[str] = []
    async with get_httpx_client() as client:

        async def task_func(
            search_query: SearchQuery,
        ):
            async with _semaphore:
                if search_query.geoid in geo_infos:
                    return
                if isinstance(search_query, StateSearchQuery):
                    search_query_str = search_query.name
                else:
                    search_query_str = f"{search_query.name}, {search_query.state}"
                results = await _get_search_results(client, search_query_str)
                for result in results:
                    geo_infos[result.geoid] = result

                if search_query.geoid not in geo_infos:
                    not_found.append(search_query.geoid)

        tasks = [
            asyncio.create_task(task_func(search_query))
            for search_query in search_queries
        ]
        await asyncio.gather(*tasks)

    logging.info("Found %d / %d results", len(geo_infos), len(search_queries))
    return list(geo_infos.values()), not_found


async def scrape_search_results(
    tiger_s3_paths: TigerPaths, s3: Any, dest_path: str
) -> tuple[list[GeoInfo], list[str]]:
    """
    Use names from tiger files to scrape search results from QuickFacts.

    Args:
        tiger_s3_paths (TigerPaths): The tiger s3 paths.
        s3 (Any): The s3 client.
        dest_path (str): The s3 path to save the scraped results. File will be named `search_results.json`.

    Returns:
        list[GeoInfo]: A list of scraped GeoInfo objects.
        list[str]: A list of GEOIDs that could not be found. QuickFacts only has data for geographies with population above 5000.
    """

    dest_file_path = os.path.join(dest_path, "search_results.json")
    # Load previous results
    try:
        response = s3.get_object(Bucket=settings.s3_bucket, Key=dest_file_path)
        previous_results = json.loads(response["Body"].read().decode("utf-8"))
        prev_geo_infos = previous_results["geo_infos"]
        prev_geo_infos_by_geoid = {
            geo_info["geoid"]: geo_info for geo_info in prev_geo_infos
        }
        prev_not_found = previous_results["not_found"]
        prev_not_found_set = set(prev_not_found)
    except Exception as e:
        logging.warning("Error loading previous search results: %s", e)
        logging.info("Missing or invalid search results file, starting fresh search")
        prev_geo_infos = []
        prev_geo_infos_by_geoid = {}
        prev_not_found = []
        prev_not_found_set = set()

    geo_infos: list[GeoInfo] = []
    not_found: list[str] = []
    search_queries: list[SearchQuery] = []
    state_geo_names: dict[str, str] = {}

    state_table = load_dbf_file_from_s3(s3, tiger_s3_paths.state)
    county_table = load_dbf_file_from_s3(s3, tiger_s3_paths.county)
    place_tables = [
        load_dbf_file_from_s3(s3, place_path) for place_path in tiger_s3_paths.places
    ]

    for row in state_table:
        if row["GEOID"] in prev_geo_infos_by_geoid:
            geo_infos.append(GeoInfo(**prev_geo_infos_by_geoid[row["GEOID"]]))
            continue
        if row["GEOID"] in prev_not_found_set:
            not_found.append(row["GEOID"])
            continue

        search_queries.append(StateSearchQuery(geoid=row["GEOID"], name=row["NAME"]))
        state_geo_names[row["GEOID"]] = row["NAME"]

    for row in county_table:
        if row["GEOID"] in prev_geo_infos_by_geoid:
            geo_infos.append(GeoInfo(**prev_geo_infos_by_geoid[row["GEOID"]]))
            continue
        if row["GEOID"] in prev_not_found_set:
            not_found.append(row["GEOID"])
            continue
        search_queries.append(
            CountySearchQuery(
                geoid=row["GEOID"],
                name=row["NAMELSAD"],
                state=state_geo_names[row["STATEFP"]],
            )
        )

    for place_table in place_tables:
        for row in place_table:
            if row["GEOID"] in prev_geo_infos_by_geoid:
                geo_infos.append(GeoInfo(**prev_geo_infos_by_geoid[row["GEOID"]]))
                continue
            if row["GEOID"] in prev_not_found_set:
                not_found.append(row["GEOID"])
                continue
            search_queries.append(
                PlaceSearchQuery(
                    geoid=row["GEOID"],
                    name=row["NAMELSAD"],
                    state=state_geo_names[row["STATEFP"]],
                )
            )

    logging.info("Total search queries: %d", len(search_queries))

    new_geo_infos, new_not_found = await _scrape_search_for_queries(search_queries)
    geo_infos.extend(new_geo_infos)
    not_found.extend(new_not_found)

    geo_infos_json = [geo_info.model_dump() for geo_info in geo_infos]
    s3.put_object(
        Bucket=settings.s3_bucket,
        Key=dest_file_path,
        Body=json.dumps(
            {
                "geo_infos": geo_infos_json,
                "not_found": not_found,
            }
        ),
    )
    return geo_infos, not_found
