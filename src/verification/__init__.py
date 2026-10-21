# src/verification/__init__.py
# Public interface of the Verification Module.

from .evidence_report import EvidenceReport, generate_evidence_report
from .taint import TaintViolation, taint_analysis

__all__ = [
    "taint_analysis",
    "TaintViolation",
    "EvidenceReport",
    "generate_evidence_report",
]
