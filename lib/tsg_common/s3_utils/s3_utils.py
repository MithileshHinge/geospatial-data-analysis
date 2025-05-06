from typing import Any, Iterator
import tempfile
from pathlib import Path
import boto3
from botocore.config import Config


def get_s3_client(region: str, endpoint: str | None = None):
    return boto3.client(
        "s3",
        region_name=region,
        endpoint_url=endpoint,
        config=Config(signature_version="s3v4"),
    )


def iter_objects(s3: Any, bucket: str, prefix: str) -> Iterator[dict]:
    """Yield S3 objects under prefix lazily (pagination-safe)."""
    kwargs = {"Bucket": bucket, "Prefix": f"{prefix}".strip("/")}
    while True:
        resp = s3.list_objects_v2(**kwargs)
        for obj in resp.get("Contents", []):
            yield obj
        if not resp.get("IsTruncated"):
            break
        kwargs["ContinuationToken"] = resp["NextContinuationToken"]


def list_s3_dir(s3: Any, bucket: str, prefix: str) -> list[str]:
    """List full paths of all files and subdirectories under prefix."""
    prefix = prefix.strip("/")
    if prefix:
        prefix = prefix + "/"

    result = set()
    kwargs = {"Bucket": bucket, "Prefix": prefix, "Delimiter": "/"}

    while True:
        resp = s3.list_objects_v2(**kwargs)
        # Add direct files with their full paths
        for obj in resp.get("Contents", []):
            key = obj["Key"]
            if key != prefix:  # Skip the prefix itself
                result.add(key)

        # Add subdirectories with their full paths
        for common_prefix in resp.get("CommonPrefixes", []):
            prefix_str = common_prefix["Prefix"]
            # Remove trailing slash for consistency
            result.add(prefix_str.rstrip("/"))

        if not resp.get("IsTruncated"):
            break
        kwargs["ContinuationToken"] = resp["NextContinuationToken"]

    return sorted(list(result))


def download_to_tempfile(s3: Any, bucket: str, key: str) -> Path:
    """Download an S3 key into a tmp dir and return the local Path."""
    tmpdir = tempfile.mkdtemp(prefix="etl_")
    local = Path(tmpdir) / Path(key).name
    s3.download_file(bucket, key, str(local))
    return local
