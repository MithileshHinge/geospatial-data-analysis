from pydantic import BaseModel


class GeoInfo(BaseModel):
    geoid: str
    id: str
    label: str
    level: str
