# src/verification/__init__.py
# Public interface of the Verification Module.

from .taint import taint_analysis, TaintViolation
from .evidence_report import EvidenceReport, generate_evidence_report

__all__ = [
    "taint_analysis",
    "TaintViolation",
    "EvidenceReport",
    "generate_evidence_report",
]
