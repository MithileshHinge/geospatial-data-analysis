from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from tsg_common.db import ReadQueries
import logging

from app.deps import get_db
from app.models.geo import NearbyPlace, NearbyResponse
from app.middleware.error_handler import APIError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["places"])


@router.get("/places/nearby", response_model=NearbyResponse)
def nearby(
    lat: float = Query(
        ..., ge=-90.0, le=90.0, description="Latitude between -90 and 90"
    ),
    lon: float = Query(
        ..., ge=-180.0, le=180.0, description="Longitude between -180 and 180"
    ),
    radius_km: int = Query(
        50, gt=0, le=500, description="Search radius in kilometers (1-500)"
    ),
    limit: int = Query(
        25, gt=0, le=100, description="Maximum number of results (1-100)"
    ),
    db: Session = Depends(get_db),
):
    try:
        logger.info(
            "Processing nearby places request",
            extra={
                "lat": lat,
                "lon": lon,
                "radius_km": radius_km,
                "limit": limit,
            },
        )

        results = ReadQueries(db).nearby_places(lat, lon, radius_km, limit)
        if not results:
            logger.info(
                "No places found in radius",
                extra={
                    "lat": lat,
                    "lon": lon,
                    "radius_km": radius_km,
                },
            )
            return NearbyResponse(results=[])

        return NearbyResponse(results=[NearbyPlace(**r) for r in results])

    except Exception as e:
        logger.error(
            "Error processing nearby places request",
            extra={
                "error": str(e),
                "lat": lat,
                "lon": lon,
                "radius_km": radius_km,
                "limit": limit,
            },
            exc_info=True,
        )
        raise APIError(
            message="Internal server error processing nearby places request",
            status_code=500,
        )
