# src/integration/langchain_adapter.py
#
# Translates a verified WorkflowAST to executable LangChain Python code.
#
# The generated code is a Python module with:
#   - A module-level docstring containing the evidence report
#   - Imports for required LangChain components
#   - A run_workflow() function implementing the steps in order
#   - Inline comments mapping each step back to its DSL op and ID
#
# The evidence report is embedded as a module docstring so it is
# visible to any engineer who opens the generated file (Critical Constraint 8).
#
# Usage:
#   from workflowsynth.integration.langchain_adapter import to_langchain_python
#   python_code = to_langchain_python(ast, evidence_report)

from ..dsl.ast_nodes import WorkflowAST, WorkflowStep
from ..verification.evidence_report import EvidenceReport


# --- LangChain component mapping ---------------------------------------------
#
# Maps each DSL op to the most appropriate LangChain component or pattern.

LANGCHAIN_COMPONENTS: dict[str, str] = {
    # Data Operations
    "fetch_api":       "requests.get",
    "filter_records":  "list comprehension",
    "transform_json":  "dict transformation",
    "validate_schema": "pydantic.BaseModel",
    "aggregate_data":  "itertools.groupby",
    "merge_datasets":  "dict merge",
    "extract_field":   "dict.get",
    "format_output":   "json.dumps",

    # Control Flow
    "route_to_step":      "if/elif branching",
    "apply_rule":         "business rule function",
    "loop_records":       "for loop",
    "parallel_execute":   "asyncio.gather",
    "wait_for_condition": "asyncio.wait_for",
    "handle_error":       "try/except",
    "retry_step":         "tenacity.retry",
    "terminate_workflow": "return/raise",

    # Integration Operations
    "send_to_queue":     "pika / aio_pika",
    "log_audit":         "logging.getLogger",
    "notify_user":       "smtplib / sendgrid",
    "call_webhook":      "requests.post",
    "read_database":     "sqlalchemy.select",
    "write_database":    "sqlalchemy.insert",
    "authenticate_user": "auth middleware",
    "encrypt_field":     "cryptography.fernet",
    "call_subworkflow":  "function call",
}


def to_langchain_python(ast: WorkflowAST, evidence_report: EvidenceReport) -> str:
    """
    Translates a verified WorkflowAST to LangChain Python code.

    Returns a Python module as a string. The module contains:
    - Evidence report as a module docstring
    - Imports
    - run_workflow() function with one section per DSL step

    Args:
        ast:            The verified WorkflowAST.
        evidence_report: The evidence report from generate_evidence_report().

    Returns:
        String containing the generated Python module.
    """
    lines = []

    # Module docstring -- evidence report
    lines += _build_module_docstring(evidence_report)

    # Imports
    lines += _build_imports(ast)
    lines.append("")
    lines.append("")

    # run_workflow() function
    lines += _build_run_workflow(ast)

    return "\n".join(lines)


# --- Section builders --------------------------------------------------------

def _build_module_docstring(evidence_report: EvidenceReport) -> list[str]:
    """Builds the module docstring containing the evidence report."""
    lines = ['"""']
    lines.append(f"WorkflowSynth Generated Workflow: {evidence_report.workflow_id}")
    lines.append(f"Generated: {evidence_report.generated_at}")
    lines.append(f"Synthesis attempts: {evidence_report.synthesis_attempts}")
    lines.append("")
    lines.append("EVIDENCE REPORT")
    lines.append("=" * 60)
    lines.append("")
    lines.append("VERIFIED:")
    for v in evidence_report.verified:
        lines.append(f"  [x] {v}")
    lines.append("")
    lines.append("NOT CHECKED:")
    for n in evidence_report.not_checked:
        lines.append(f"  [ ] {n}")
    lines.append("")
    lines.append("ENGINEER RESPONSIBILITIES (review before deploying):")
    for r in evidence_report.engineer_responsibilities:
        lines.append(f"  --> {r}")
    lines.append('"""')
    lines.append("")
    return lines


def _build_imports(ast: WorkflowAST) -> list[str]:
    """Builds the import section based on ops present in the workflow."""
    imports = ["import logging", "from typing import Any, Dict, List, Optional"]
    ops = {s.op for s in ast.steps}

    if "fetch_api" in ops or "call_webhook" in ops or "authenticate_user" in ops:
        imports.append("import requests")
    if "validate_schema" in ops:
        imports.append("from pydantic import BaseModel, ValidationError")
    if "read_database" in ops or "write_database" in ops:
        imports.append("from sqlalchemy import create_engine, text")
    if "parallel_execute" in ops or "wait_for_condition" in ops:
        imports.append("import asyncio")
    if "retry_step" in ops:
        imports.append("from tenacity import retry, stop_after_attempt, wait_fixed")
    if "encrypt_field" in ops:
        imports.append("from cryptography.fernet import Fernet")
    if "send_to_queue" in ops:
        imports.append("import pika")
    if "log_audit" in ops:
        imports.append("import logging")

    imports.append("")
    imports.append("logger = logging.getLogger(__name__)")

    return imports


def _build_run_workflow(ast: WorkflowAST) -> list[str]:
    """Builds the run_workflow() function."""
    lines = [
        f"def run_{ast.workflow_id}(context: Dict[str, Any]) -> Dict[str, Any]:",
        f'    """',
        f"    Execute the {ast.workflow_id} workflow.",
        f"    Generated by WorkflowSynth. Review evidence report above before deploying.",
        f'    """',
        "    state: Dict[str, Any] = {}",
        "",
    ]

    for step in ast.steps:
        lines += _build_step(step)
        lines.append("")

    lines.append("    return state")
    return lines


def _build_step(step: WorkflowStep) -> list[str]:
    """Builds the code block for a single step."""
    component = LANGCHAIN_COMPONENTS.get(step.op, "# TODO: implement")
    lines = [
        f"    # Step: {step.id} | op: {step.op} | component: {component}",
    ]

    # Add params as comments for engineer reference
    if step.params:
        for k, v in step.params.items():
            lines.append(f"    # param {k}: {v}")

    # Generate a stub implementation with the output variable
    if step.output:
        lines.append(
            f"    {step.output} = _execute_{step.op}("
            f"context, state, {repr(step.params)})"
        )
        lines.append(f"    state['{step.output}'] = {step.output}")
    else:
        lines.append(
            f"    _execute_{step.op}(context, state, {repr(step.params)})"
        )

    return lines
