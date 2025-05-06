from typing import Any
import csv
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    before_sleep_log,
)
import logging
import httpx
import asyncio
import ssl
import certifi
import zipfile
import io
from dbfread import DBF
import tempfile

from settings import settings

_semaphore = asyncio.BoundedSemaphore(settings.dl_concurrency)


@retry(
    wait=wait_random_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(5),
    before_sleep=before_sleep_log(logging.getLogger(__name__), logging.WARNING),
)
async def fetch_with_retries(client: httpx.AsyncClient, url: str) -> bytes:
    headers = {
        "accept": "application/json",
        "accept-language": "en-US,en;q=0.9",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    }
    r = await client.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.content


def get_httpx_client():
    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    limits = httpx.Limits(
        max_connections=settings.dl_concurrency,
        max_keepalive_connections=settings.dl_concurrency,
    )
    return httpx.AsyncClient(
        follow_redirects=True, verify=ssl_ctx, limits=limits, timeout=30
    )


async def download_file_to_s3(
    client: httpx.AsyncClient, s3: Any, url: str, dest_path: str
) -> str:
    logging.debug("Downloading file %s to %s", url, dest_path)
    async with _semaphore:
        # Check if file already exists in S3
        try:
            s3.head_object(Bucket=settings.s3_bucket, Key=dest_path)
            logging.debug("File %s already exists in S3, skipping download", dest_path)
            return dest_path
        except s3.exceptions.ClientError as e:
            if e.response["Error"]["Code"] != "404":
                raise e  # Re-raise if it's not a "not found" error

        # Download file
        body = await fetch_with_retries(client, url)

        # Upload the file to s3
        s3.put_object(Bucket=settings.s3_bucket, Key=dest_path, Body=body)
        logging.debug("Downloaded file %s\nbytes: %d", dest_path, len(body))

        return dest_path


async def batch_download_files_to_s3(
    client: httpx.AsyncClient,
    s3: Any,
    urls_to_dest_path: dict[str, str],
) -> list[str]:
    """
    Download files from the internet and upload them to S3.

    Args:
        client (httpx.AsyncClient): The httpx client.
        s3 (boto3.client): The S3 client.
        urls_to_dest_path (dict[str, str]): A dictionary of URLs to destination paths. Destination paths are relative to the S3 bucket root.

    Returns:
        list[str]: A list of S3 paths to the downloaded files, relative to the S3 bucket root.
    """
    if not urls_to_dest_path:
        return []
    tasks = [
        asyncio.create_task(
            download_file_to_s3(
                client,
                s3,
                url,
                dest_path,
            )
        )
        for url, dest_path in urls_to_dest_path.items()
    ]
    return await asyncio.gather(*tasks)


def load_dbf_file_from_s3(s3: Any, s3_path: str) -> DBF:
    logging.info("Loading DBF file from S3: %s", s3_path)
    response = s3.get_object(Bucket=settings.s3_bucket, Key=s3_path)
    zip_content = response["Body"].read()

    with zipfile.ZipFile(io.BytesIO(zip_content)) as zip_file:
        dbf_filename = [n for n in zip_file.namelist() if n.endswith(".dbf")][0]
        with zip_file.open(dbf_filename) as dbf_file:
            # Create a temporary file and write the DBF content to it
            with tempfile.NamedTemporaryFile(suffix=".dbf", delete=True) as temp_file:
                temp_file.write(dbf_file.read())
                temp_file.flush()
                temp_file_path = temp_file.name
                return DBF(temp_file_path, load=True, encoding="utf-8")


def load_dbf_file_from_zip(zip_file_path: str) -> DBF:
    logging.info("Loading DBF file from zip: %s", zip_file_path)
    with zipfile.ZipFile(zip_file_path) as zip_file:
        dbf_filename = [n for n in zip_file.namelist() if n.endswith(".dbf")][0]
        with zip_file.open(dbf_filename) as dbf_file:
            # Create a temporary file and write the DBF content to it
            with tempfile.NamedTemporaryFile(suffix=".dbf", delete=True) as temp_file:
                temp_file.write(dbf_file.read())
                temp_file.flush()
                temp_file_path = temp_file.name
                return DBF(temp_file_path, load=True, encoding="utf-8")


def load_csv_file_from_s3(s3: Any, s3_path: str) -> list[list[str]]:
    logging.info("Loading CSV file from S3: %s", s3_path)
    response = s3.get_object(Bucket=settings.s3_bucket, Key=s3_path)
    csv_content = response["Body"].read().decode("utf-8")
    reader = csv.reader(csv_content.splitlines())
    return [row for row in reader]


def write_csv_file_to_s3(s3: Any, s3_path: str, csv_content: list[list[str]]):
    logging.info("Writing CSV file to S3: %s", s3_path)
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=True) as temp_file:
        with open(temp_file.name, "w") as f:
            writer = csv.writer(f)
            writer.writerows(csv_content)
        s3.put_object(Bucket=settings.s3_bucket, Key=s3_path, Body=temp_file.read())
