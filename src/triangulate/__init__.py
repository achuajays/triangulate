"""triangulate: find where your sources disagree — before someone has to find out the hard way."""

from .base import Backend, Point
from .extractor import Extractor
from .aligner import Aligner
from .conflict import ConflictScan
from .result import DimensionView, Result
from .api import Triangulate
from .version import __version__

__all__ = [
    "Triangulate",
    "Extractor",
    "Aligner",
    "ConflictScan",
    "Result",
    "DimensionView",
    "Backend",
    "Point",
    "__version__",
]
