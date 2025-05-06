from fastapi import APIRouter, Depends, Path, Query, Response
from sqlalchemy.orm import Session
from tsg_common.cache import Cache
from tsg_common.db import ReadQueries
import logging

from app.deps import get_db, get_cache
from app.models.geo import LayerLiteral
from app.middleware.error_handler import APIError
from app.settings import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["tiles"])


@router.get("/tiles/{layer}/{z}/{x}/{y}.{ext}")
def vector_tile(
    layer: LayerLiteral,
    z: int = Path(..., ge=0, le=22, description="Zoom level between 0 and 22"),
    x: int = Path(..., ge=0, description="X coordinate (must be non-negative)"),
    y: int = Path(..., ge=0, description="Y coordinate (must be non-negative)"),
    ext: str = Path(
        ..., pattern="^(mvt|geojson)$", description="File extension (mvt or geojson)"
    ),
    simplify: int | None = Query(
        None, ge=0, description="Simplification factor (optional)"
    ),
    db: Session = Depends(get_db),
    cache: Cache = Depends(get_cache),
):
    try:
        # content-type
        mime = (
            "application/vnd.mapbox-vector-tile"
            if ext == "mvt"
            else "application/geo+json"
        )

        # Validate tile coordinates at zoom level
        max_tile = 2**z - 1
        if x > max_tile or y > max_tile:
            logger.warning(
                "Invalid tile coordinates",
                extra={
                    "layer": layer,
                    "z": z,
                    "x": x,
                    "y": y,
                    "max_tile": max_tile,
                },
            )
            raise APIError(
                message="Invalid tile coordinates for zoom level",
                status_code=400,
                details={
                    "max_x": max_tile,
                    "max_y": max_tile,
                    "zoom": z,
                },
            )

        key = f"tile:{layer}:{z}:{x}:{y}:{ext}"
        data = cache.get_raw(key)

        if data is None:
            logger.info(
                "Cache miss for tile",
                extra={
                    "layer": layer,
                    "z": z,
                    "x": x,
                    "y": y,
                    "ext": ext,
                },
            )
            tile = ReadQueries(db).tile_data(layer, z, x, y, format=ext)
            if tile is None:
                raise APIError(
                    message="Tile not found",
                    status_code=404,
                )
            data = tile if isinstance(tile, (bytes, bytearray)) else str(tile).encode()
            settings = get_settings()
            cache.set_raw(key, data, ttl=settings.tiles_cache_ttl)

        return Response(content=data, media_type=mime)

    except Exception as e:
        if isinstance(e, APIError):
            raise
        logger.error(
            "Error processing tile request",
            extra={
                "error": str(e),
                "layer": layer,
                "z": z,
                "x": x,
                "y": y,
                "ext": ext,
            },
            exc_info=True,
        )
        raise APIError(
            message="Internal server error processing tile",
            status_code=500,
        )
