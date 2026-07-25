"""Backward-compat shim -- moved to sdlc_pipeline/review_criteria.py."""

import warnings as _w

_w.warn(
    "Import from langgraph_engine.review_criteria is deprecated. "
    "Use langgraph_engine.sdlc_pipeline.review_criteria instead.",
    DeprecationWarning,
    stacklevel=2,
)
from .sdlc_pipeline.review_criteria import *  # noqa: E402,F401,F403
