from pydantic import BaseModel
from typing import Any, Sequence

from tsg_common.s3_utils import iter_objects, list_s3_dir

from settings import settings


class TigerS3Paths(BaseModel):
    """Model to hold TIGER s3 paths organized by type."""

    international: str
    state: str
    county: str
    cbsa: str
    places: Sequence[str]

    @classmethod
    def from_base_s3_path(cls, s3: Any, base_s3_path: str) -> "TigerS3Paths":
        """
        Create a TigerS3Paths instance from base s3 path.

        Args:
            s3: The s3 client to use.
            base_s3_path: The base s3 path which contains the TIGER20XX directory.

        Returns:
            A TigerS3Paths instance.
        """

        # Get TIGER20XX directory
        tiger_dir_path = list_s3_dir(s3, settings.s3_bucket, base_s3_path)[0]

        # Fetch place files dynamically
        place_files: list[str] = []
        place_base_path = f"{tiger_dir_path}/PLACE/"
        for place_obj in iter_objects(s3, settings.s3_bucket, place_base_path):
            if place_obj["Key"].endswith(".zip"):
                place_files.append(place_obj["Key"])

        international_path = list_s3_dir(
            s3, settings.s3_bucket, f"{tiger_dir_path}/INTERNATIONALBOUNDARY/"
        )[0]
        state_path = list_s3_dir(s3, settings.s3_bucket, f"{tiger_dir_path}/STATE/")[0]
        county_path = list_s3_dir(s3, settings.s3_bucket, f"{tiger_dir_path}/COUNTY/")[
            0
        ]
        cbsa_path = list_s3_dir(s3, settings.s3_bucket, f"{tiger_dir_path}/CBSA/")[0]

        return cls(
            international=international_path,
            state=state_path,
            county=county_path,
            cbsa=cbsa_path,
            places=place_files,
        )
