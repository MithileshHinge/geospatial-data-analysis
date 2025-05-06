from typing import Literal, Sequence

from pydantic import BaseModel, Field


LayerLiteral = Literal["states", "counties", "msas", "places"]


class NearbyPlace(BaseModel):
    geoid: str
    name: str
    lat: float
    lon: float
    distance_km: float = Field(..., ge=0)


class NearbyResponse(BaseModel):
    results: Sequence[NearbyPlace]


class ReverseCounty(BaseModel):
    geoid: str
    name: str


class ReverseMSA(BaseModel):
    geoid: str
    name: str


class ReverseResponse(BaseModel):
    county: ReverseCounty | None = None
    msa: ReverseMSA | None = None
