from pydantic import BaseModel
import httpx
from bs4 import BeautifulSoup
from typing import cast, Sequence


class TigerPaths(BaseModel):
    """Model to hold TIGER paths organized by type."""

    international: str
    state: str
    county: str
    cbsa: str
    places: Sequence[str]

    @classmethod
    async def from_base_url(
        cls, client: httpx.AsyncClient, base_url: str, year: str
    ) -> "TigerPaths":
        """Create a TigerPaths instance from base URL and year."""
        # Fetch place files dynamically
        place_url = f"{base_url}/TIGER{year}/PLACE/"
        response = await client.get(place_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        place_files = [
            f"{base_url}/TIGER{year}/PLACE/{a['href']}"
            for a in soup.select("table td a")
            if cast(str, a["href"]).endswith(".zip")
        ]

        return cls(
            international=f"{base_url}/TIGER{year}/INTERNATIONALBOUNDARY/tl_{year}_us_internationalboundary.zip",
            state=f"{base_url}/TIGER{year}/STATE/tl_{year}_us_state.zip",
            county=f"{base_url}/TIGER{year}/COUNTY/tl_{year}_us_county.zip",
            cbsa=f"{base_url}/TIGER{year}/CBSA/tl_{year}_us_cbsa.zip",
            places=place_files,
        )
