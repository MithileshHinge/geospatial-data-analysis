from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from tsg_common.db import ReadQueries
import logging

from app.deps import get_db
from app.models.geo import ReverseResponse
from app.middleware.error_handler import APIError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["reverse"])


@router.get("/reverse", response_model=ReverseResponse)
def reverse_lookup(
    lat: float = Query(
        ..., ge=-90.0, le=90.0, description="Latitude between -90 and 90"
    ),
    lon: float = Query(
        ..., ge=-180.0, le=180.0, description="Longitude between -180 and 180"
    ),
    layers: str = Query(
        "counties,msas",
        description="Comma-separated list of layers to search (counties,msas)",
        pattern="^[a-z,]+$",
    ),
    db: Session = Depends(get_db),
):
    try:
        logger.info(
            "Processing reverse geocoding request",
            extra={
                "lat": lat,
                "lon": lon,
                "layers": layers,
            },
        )

        layer_tuple = tuple(filter(None, layers.split(",")))
        if not layer_tuple:
            raise APIError(
                message="No valid layers specified",
                status_code=400,
                details={"layers": "Must specify at least one layer"},
            )

        result = ReadQueries(db).reverse_lookup(lat, lon, layer_tuple)
        if not any(getattr(result, layer, None) for layer in ("county", "msa")):
            logger.info(
                "No results found for location",
                extra={
                    "lat": lat,
                    "lon": lon,
                    "layers": layers,
                },
            )

        return result

    except Exception as e:
        if isinstance(e, APIError):
            raise
        logger.error(
            "Error processing reverse geocoding request",
            extra={
                "error": str(e),
                "lat": lat,
                "lon": lon,
                "layers": layers,
            },
            exc_info=True,
        )
        raise APIError(
            message="Internal server error processing reverse geocoding request",
            status_code=500,
        )
