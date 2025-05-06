from pydantic import BaseModel
from typing import Literal


class BaseSearchQuery(BaseModel):
    geoid: str
    name: str


class StateSearchQuery(BaseSearchQuery):
    level: Literal["state"] = "state"
    pass


class CountySearchQuery(BaseSearchQuery):
    level: Literal["county"] = "county"
    state: str


class PlaceSearchQuery(BaseSearchQuery):
    level: Literal["place"] = "place"
    state: str


SearchQuery = StateSearchQuery | CountySearchQuery | PlaceSearchQuery
