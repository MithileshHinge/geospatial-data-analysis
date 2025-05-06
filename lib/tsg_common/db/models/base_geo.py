from sqlalchemy import Column
from geoalchemy2 import Geometry

from ..base import Base


class BaseGeo(Base):
    """Base class for all geographic models.

    This class provides the basic geometric column that is shared
    across all geographic models.
    """

    __abstract__ = True

    geom = Column(Geometry("MULTIPOLYGON", srid=4326), nullable=False)
