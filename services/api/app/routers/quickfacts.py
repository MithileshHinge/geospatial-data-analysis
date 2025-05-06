from fastapi import APIRouter, Depends, Path, HTTPException
from sqlalchemy.orm import Session
from tsg_common.cache import Cache
from tsg_common.db import ReadQueries
from app.deps import get_db, get_cache
from app.models.geo import LayerLiteral
from app.settings import get_settings

router = APIRouter(prefix="/v1", tags=["quickfacts"])


@router.get("/quickfacts/{layer}/{geoid}")
def quickfacts(
    layer: LayerLiteral = Path(..., description="states|counties|places"),
    geoid: str = Path(..., min_length=2, max_length=7),
    db: Session = Depends(get_db),
    cache: Cache = Depends(get_cache),
):
    key = f"qf:{layer}:{geoid}"
    settings = get_settings()

    data = cache.get_or_set(
        key,
        settings.quickfacts_cache_ttl,
        lambda: ReadQueries(db).get_quickfacts(layer, geoid),
    )
    if data is None:
        raise HTTPException(status_code=404, detail="QuickFacts not found")
    return data
