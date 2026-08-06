# src/verification/__init__.py
# Public interface of the Verification Module.

from .taint import taint_analysis, TaintViolation

__all__ = [
    "taint_analysis",
    "TaintViolation",
]
