import logging

from tsg_common.db.engine import SessionLocal
from tsg_common.cache import Cache

logger = logging.getLogger(__name__)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_cache() -> Cache:
    logger.info("Initializing cache connection")
    try:
        cache = Cache()
        logger.info("Cache connection initialized successfully")
        return cache
    except Exception as e:
        logger.error(f"Failed to initialize cache: {str(e)}", exc_info=True)
        raise
