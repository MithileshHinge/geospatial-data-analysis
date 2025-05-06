from fastapi import APIRouter, status, Response, Depends
from sqlalchemy.orm import Session
import logging

from tsg_common.db import ReadQueries
from app.deps import get_db
from app.middleware.error_handler import APIError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["infra"])


@router.get("/healthz", status_code=status.HTTP_204_NO_CONTENT)
def healthz(db: Session = Depends(get_db)) -> Response:
    try:
        logger.debug("Running health check")
        read_queries = ReadQueries(db)
        read_queries.health_check()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except Exception as e:
        logger.error(
            "Health check failed",
            extra={"error": str(e)},
            exc_info=True,
        )
        raise APIError(
            message="Health check failed",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"error": str(e)},
        )
