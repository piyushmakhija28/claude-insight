"""Backward-compat shim -- re-exported from sdlc_pipeline/call_graph_analyzer.py."""

import warnings as _w

_w.warn(
    "Import from langgraph_engine.analysis.call_graph_analyzer is deprecated. "
    "Use langgraph_engine.sdlc_pipeline.call_graph_analyzer instead.",
    DeprecationWarning,
    stacklevel=2,
)
from langgraph_engine.sdlc_pipeline.call_graph_analyzer import *  # noqa: E402,F401,F403
