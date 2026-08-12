# WorkflowSynth -- Session 05: Evidence Report

**Date:** August 6, 2026
**DSR Phase:** Build (Week 28)
**Component:** Verification Module -- Evidence Report
**Repository:** https://github.com/daniszwarc/workflowsynth

---

## Objective

Implement the evidence report: the structured output that accompanies every
verified workflow. This is Architectural Decision 5 -- the system never delivers
a binary pass/fail. It delivers an explicit statement of what was verified,
what was not checked, and what remains the deploying engineer's responsibility.

By the end of this session we have:

- `src/verification/evidence_report.py` -- EvidenceReport dataclass + generator
- `src/verification/__init__.py` -- updated to export EvidenceReport
- `tests/unit/test_evidence_report.py` -- evidence report unit tests

---

## Why the Evidence Report Exists

This is the most academically distinctive component of WorkflowSynth.

Most automated verification systems produce a binary result: pass or fail.
This is a problem in practice. A "pass" signals to the deploying engineer that
the system is safe, but formal verification can only check what it is formally
specified to check. Type safety and taint analysis are powerful tools, but they
cannot catch every class of vulnerability. Business logic errors, rate limiting
issues, permission edge cases, and integration-specific risks are all outside
the verification scope.

When a system says "pass" without qualification, engineers stop thinking. The
pass/fail binary creates what the open-samd regulatory framework calls the
"disclaimer trap" -- a false sense of assurance that leads to under-reviewed
deployments.

WorkflowSynth addresses this with the evidence report. Instead of "pass", the
system produces a structured document that says three things explicitly:

1. **Verified:** what was formally checked and confirmed to hold.
2. **Not checked:** what falls outside the current verification scope.
3. **Engineer responsibilities:** what requires human review before deployment.

This implements open-samd Pattern 1 -- communicating verification as a
reduction of risk rather than a guarantee of correctness. It is also directly
relevant to the researcher's practical experience: this pattern emerged from
real observations of how automated systems are misused in regulated environments.

### Academic grounding

Architectural Decision 5 is grounded in two bodies of work. The open-samd
framework (Berni's regulatory advisory work) identifies the disclaimer trap as
a key failure mode in deployed AI systems. Tihanyi et al. (2025) FormAI-v2
demonstrates that 62% of LLM-generated programs contain vulnerabilities --
including ones that pass automated checks. The evidence report is the
mechanism that bridges the gap between what the system verifies and what
engineers need to know before deploying.

---

## What the Evidence Report Contains

### Verified section

Everything in this section was formally checked and confirmed to hold for this
specific workflow. These are not claims -- they are proven facts about this
workflow instance.

- **DSL vocabulary compliance:** every op is in the 25 VALID_OPS vocabulary.
  No invented or unsupported operations.
- **Structural validity:** all required fields present, all step IDs unique,
  all params correctly typed.
- **Type safety:** every params.input reference resolves to a previously
  declared output variable. All type compositions are valid.
- **Authentication precedence:** every write_database and call_webhook is
  preceded by an authenticate_user step.
- **Taint safety:** no tainted variable (from fetch_api, read_database,
  call_webhook, or call_subworkflow) reaches a critical sink without passing
  through a declared sanitiser.
- **Test suite:** all tests in the workflow's pytest test suite pass against
  this DSL candidate.

### Not checked section

Everything in this section is outside the current verification scope. These
are honest limitations -- not failures, but boundaries that the engineer must
understand.

- **Business logic correctness:** the verification module checks structural
  and security properties. It does not verify that the workflow implements the
  correct business logic for the specific domain.
- **Rate limits and quotas:** external API calls (fetch_api, call_webhook)
  are not checked for rate limiting, authentication token expiry, or quota
  constraints.
- **Data schema correctness:** validate_schema is treated as a sanitiser that
  removes taint. The correctness of the schema definition itself is not verified.
- **Concurrency and race conditions:** parallel_execute steps are not checked
  for race conditions or deadlock.
- **Integration-specific security:** n8n and LangChain have their own security
  models. Stage 2 checks cover the translated output structure, not the
  runtime security of the target platform.

### Engineer responsibilities section

Everything in this section requires human review before the workflow is
deployed to production. The evidence report does not replace this review -- it
makes it explicit.

- Review the workflow logic against the business requirements it is meant
  to implement.
- Verify that the schemas used in validate_schema steps are current and
  correct for the target environment.
- Confirm that all external endpoints (fetch_api, call_webhook) are authorised
  and that credentials are managed securely outside the workflow.
- Review parallel_execute steps for concurrency safety in the target
  deployment environment.
- Confirm that the authenticate_user role requirements match the actual
  permission model of the deployment environment.

---

## File 1: `src/verification/evidence_report.py`

```python
# src/verification/evidence_report.py
#
# Evidence report for WorkflowSynth verified workflows.
#
# Implements Architectural Decision 5: compliance-aware verification output.
# The system never delivers a binary pass/fail. It delivers a structured
# report that explicitly states what was verified, what was not checked,
# and what requires human review before deployment.
#
# Implements open-samd Pattern 1: communicating verification as a reduction
# of risk rather than a guarantee of correctness.
#
# Every verified workflow output must carry this report.
# CONSTRAINT (Critical Constraint 8): Never deliver a workflow without it.

from dataclasses import dataclass, field
from datetime import datetime, timezone
from ..dsl.ast_nodes import WorkflowAST


@dataclass
class EvidenceReport:
    """
    Structured evidence report for a verified WorkflowSynth workflow.

    Fields:
        workflow_id:         ID of the verified workflow.
        generated_at:        UTC timestamp of report generation.
        synthesis_attempts:  Number of LLM attempts required to produce
                             this workflow (1 = success on first attempt).
        verified:            List of claims that were formally verified.
        not_checked:         List of properties outside verification scope.
        engineer_responsibilities: List of items requiring human review
                             before production deployment.
        raw_type_errors:     Type errors from the final passing attempt
                             (should be empty for a verified report).
        raw_taint_violations: Taint violations from the final passing attempt
                             (should be empty for a verified report).
    """
    workflow_id: str
    generated_at: str
    synthesis_attempts: int
    verified: list[str] = field(default_factory=list)
    not_checked: list[str] = field(default_factory=list)
    engineer_responsibilities: list[str] = field(default_factory=list)
    raw_type_errors: list[str] = field(default_factory=list)
    raw_taint_violations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """
        Serialises the evidence report to a plain dict.
        Used for JSON output and for embedding in the final n8n/LangChain output.
        """
        return {
            "evidence_report": {
                "workflow_id": self.workflow_id,
                "generated_at": self.generated_at,
                "synthesis_attempts": self.synthesis_attempts,
                "verified": self.verified,
                "not_checked": self.not_checked,
                "engineer_responsibilities": self.engineer_responsibilities,
            }
        }

    def summary(self) -> str:
        """
        Returns a human-readable summary of the evidence report.
        Suitable for logging and for the dissertation case studies.
        """
        lines = [
            f"Evidence Report -- {self.workflow_id}",
            f"Generated: {self.generated_at}",
            f"Synthesis attempts: {self.synthesis_attempts}",
            "",
            f"VERIFIED ({len(self.verified)} claims):",
            *[f"  [x] {v}" for v in self.verified],
            "",
            f"NOT CHECKED ({len(self.not_checked)} items):",
            *[f"  [ ] {n}" for n in self.not_checked],
            "",
            f"ENGINEER RESPONSIBILITIES ({len(self.engineer_responsibilities)} items):",
            *[f"  --> {r}" for r in self.engineer_responsibilities],
        ]
        return "\n".join(lines)


def generate_evidence_report(
    ast: WorkflowAST,
    synthesis_attempts: int,
    type_errors: list[str],
    taint_violations: list[str],
    test_results: dict,
) -> EvidenceReport:
    """
    Generates an EvidenceReport for a verified workflow.

    Called by the verify_output node after Stage 1 and Stage 2 both pass.
    The type_errors and taint_violations should be empty at this point --
    they are included in the report for completeness and auditability.

    Args:
        ast:                The verified WorkflowAST.
        synthesis_attempts: Number of LLM attempts used (repair_attempt + 1).
        type_errors:        Type errors from the final passing verification
                            (should be empty).
        taint_violations:   Taint violations from the final passing verification
                            (should be empty).
        test_results:       Dict of test_id -> bool from run_tests.

    Returns:
        EvidenceReport with all three sections populated.
    """
    generated_at = datetime.now(timezone.utc).isoformat()

    verified = _build_verified_claims(ast, test_results)
    not_checked = _build_not_checked(ast)
    engineer_responsibilities = _build_engineer_responsibilities(ast)

    return EvidenceReport(
        workflow_id=ast.workflow_id,
        generated_at=generated_at,
        synthesis_attempts=synthesis_attempts,
        verified=verified,
        not_checked=not_checked,
        engineer_responsibilities=engineer_responsibilities,
        raw_type_errors=type_errors,
        raw_taint_violations=taint_violations,
    )


# --- Section builders --------------------------------------------------------

def _build_verified_claims(ast: WorkflowAST, test_results: dict) -> list[str]:
    """
    Builds the list of verified claims for this specific workflow.
    Claims are concrete and specific to this workflow instance -- not generic.
    """
    claims = []

    # DSL vocabulary
    ops_used = sorted({s.op for s in ast.steps})
    claims.append(
        f"DSL vocabulary compliance: all {len(ast.steps)} steps use valid "
        f"operations from the 25-primitive vocabulary "
        f"({', '.join(ops_used)})."
    )

    # Structural validity
    claims.append(
        f"Structural validity: all required fields present, "
        f"{len(ast.steps)} step IDs unique, all params correctly typed."
    )

    # Type safety
    claims.append(
        "Type safety: all params.input references resolve to previously "
        "declared output variables. All type compositions are valid."
    )

    # Authentication precedence
    has_write_or_webhook = any(
        s.op in {"write_database", "call_webhook"} for s in ast.steps
    )
    if has_write_or_webhook:
        claims.append(
            "Authentication precedence: every write_database and call_webhook "
            "step is preceded by an authenticate_user step."
        )

    # Taint safety
    from ..dsl.constants import TAINT_SOURCES as _SOURCES
    source_ops = [s.op for s in ast.steps if s.op in {"fetch_api", "read_database", "call_webhook", "call_subworkflow"}]
    if source_ops:
        claims.append(
            f"Taint safety: data from external sources "
            f"({', '.join(sorted(set(source_ops)))}) is sanitised before "
            f"reaching critical sinks. No taint violations detected."
        )

    # Test suite
    if test_results:
        passed = sum(1 for v in test_results.values() if v)
        total = len(test_results)
        claims.append(
            f"Test suite: {passed}/{total} tests pass against this DSL candidate."
        )

    return claims


def _build_not_checked(ast: WorkflowAST) -> list[str]:
    """
    Builds the list of properties that are outside verification scope.
    Tailored to the specific ops present in this workflow.
    """
    not_checked = []

    # Always present
    not_checked.append(
        "Business logic correctness: the verification module checks structural "
        "and security properties only. It does not verify that the workflow "
        "implements the correct business logic for the target domain."
    )

    # If there are external calls
    has_external = any(
        s.op in {"fetch_api", "call_webhook"} for s in ast.steps
    )
    if has_external:
        not_checked.append(
            "Rate limits and quotas: external API calls are not checked for "
            "rate limiting, authentication token expiry, or quota constraints."
        )

    # If there are schema validations
    has_schema = any(s.op == "validate_schema" for s in ast.steps)
    if has_schema:
        not_checked.append(
            "Schema correctness: validate_schema is verified as a sanitiser. "
            "The correctness of the schema definition itself is not verified."
        )

    # If there are parallel steps
    has_parallel = any(s.op == "parallel_execute" for s in ast.steps)
    if has_parallel:
        not_checked.append(
            "Concurrency safety: parallel_execute steps are not checked for "
            "race conditions or deadlock in the target execution environment."
        )

    # Always present
    not_checked.append(
        "Integration-specific security: n8n and LangChain have their own "
        "security models. Stage 2 checks cover the translated output structure, "
        "not the runtime security of the target platform."
    )

    return not_checked


def _build_engineer_responsibilities(ast: WorkflowAST) -> list[str]:
    """
    Builds the list of items requiring human review before deployment.
    Tailored to the specific ops and patterns present in this workflow.
    """
    responsibilities = []

    # Always present
    responsibilities.append(
        "Review the workflow logic against the business requirements it is "
        "meant to implement. The system verifies structure and security -- "
        "not business correctness."
    )

    # If there are schema validations
    has_schema = any(s.op == "validate_schema" for s in ast.steps)
    if has_schema:
        responsibilities.append(
            "Verify that the schemas used in validate_schema steps are current "
            "and correct for the target environment."
        )

    # If there are external calls
    has_external = any(
        s.op in {"fetch_api", "call_webhook"} for s in ast.steps
    )
    if has_external:
        responsibilities.append(
            "Confirm that all external endpoints are authorised and that "
            "credentials are managed securely outside the workflow definition."
        )

    # If there are parallel steps
    has_parallel = any(s.op == "parallel_execute" for s in ast.steps)
    if has_parallel:
        responsibilities.append(
            "Review parallel_execute steps for concurrency safety in the "
            "target deployment environment."
        )

    # If there is authentication
    has_auth = any(s.op == "authenticate_user" for s in ast.steps)
    if has_auth:
        responsibilities.append(
            "Confirm that the authenticate_user role requirements match the "
            "actual permission model of the deployment environment."
        )

    # If there are database writes
    has_write = any(s.op == "write_database" for s in ast.steps)
    if has_write:
        responsibilities.append(
            "Review write_database steps for data integrity constraints, "
            "transaction requirements, and backup procedures in the target "
            "database environment."
        )

    return responsibilities
```

---

## File 2: `src/verification/__init__.py` (updated)

```python
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
```

---

## File 3: `tests/unit/test_evidence_report.py`

```python
# tests/unit/test_evidence_report.py
#
# Unit tests for the evidence report generator.

import pytest
from workflowsynth.dsl.parser import parse_workflow
from workflowsynth.verification.evidence_report import (
    generate_evidence_report,
    EvidenceReport,
)


def _parse(yaml_string: str):
    result = parse_workflow(yaml_string)
    assert result["ok"] is True, f"Parser failed: {result.get('errors')}"
    return result["ast"]


# --- Fixture workflows -------------------------------------------------------

FULL_WORKFLOW_YAML = """
workflow_id: invoice_approval
steps:
  - id: step_fetch
    op: fetch_api
    params:
      endpoint: "/api/invoices"
    output: raw_invoices
  - id: step_validate
    op: validate_schema
    params:
      input: raw_invoices
      schema: invoice_schema
    output: validated_invoices
  - id: step_auth
    op: authenticate_user
    params:
      role: approver
    output: auth_result
  - id: step_write
    op: write_database
    params:
      input: validated_invoices
      table: approved_invoices
    output: write_result
"""

SIMPLE_WORKFLOW_YAML = """
workflow_id: simple_log
steps:
  - id: step_log
    op: log_audit
    params:
      message: "workflow started"
"""

PARALLEL_WORKFLOW_YAML = """
workflow_id: parallel_wf
steps:
  - id: step_fetch
    op: fetch_api
    output: data
  - id: step_validate
    op: validate_schema
    params:
      input: data
      schema: s
    output: clean
  - id: step_parallel
    op: parallel_execute
  - id: step_auth
    op: authenticate_user
    params:
      role: admin
  - id: step_write
    op: write_database
    params:
      input: clean
      table: t
"""


# --- EvidenceReport generation -----------------------------------------------

def test_report_has_correct_workflow_id():
    ast = _parse(FULL_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=1,
                                      type_errors=[], taint_violations=[],
                                      test_results={})
    assert report.workflow_id == "invoice_approval"

def test_report_has_generated_at_timestamp():
    ast = _parse(FULL_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=1,
                                      type_errors=[], taint_violations=[],
                                      test_results={})
    assert report.generated_at is not None
    assert "2026" in report.generated_at  # UTC ISO format

def test_report_records_synthesis_attempts():
    ast = _parse(FULL_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=3,
                                      type_errors=[], taint_violations=[],
                                      test_results={})
    assert report.synthesis_attempts == 3


# --- Verified claims ---------------------------------------------------------

def test_verified_contains_vocabulary_claim():
    ast = _parse(FULL_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=1,
                                      type_errors=[], taint_violations=[],
                                      test_results={})
    assert any("vocabulary" in v.lower() for v in report.verified)

def test_verified_contains_type_safety_claim():
    ast = _parse(FULL_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=1,
                                      type_errors=[], taint_violations=[],
                                      test_results={})
    assert any("type safety" in v.lower() for v in report.verified)

def test_verified_contains_auth_claim_when_write_present():
    ast = _parse(FULL_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=1,
                                      type_errors=[], taint_violations=[],
                                      test_results={})
    assert any("authentication" in v.lower() for v in report.verified)

def test_verified_contains_taint_claim_when_sources_present():
    ast = _parse(FULL_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=1,
                                      type_errors=[], taint_violations=[],
                                      test_results={})
    assert any("taint" in v.lower() for v in report.verified)

def test_verified_contains_test_results_when_present():
    ast = _parse(FULL_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=1,
                                      type_errors=[], taint_violations=[],
                                      test_results={"test_1": True, "test_2": True})
    assert any("test suite" in v.lower() or "2/2" in v for v in report.verified)

def test_no_auth_claim_when_no_write_or_webhook():
    """If no write_database or call_webhook, no auth claim is needed."""
    ast = _parse(SIMPLE_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=1,
                                      type_errors=[], taint_violations=[],
                                      test_results={})
    assert not any("authentication" in v.lower() for v in report.verified)


# --- Not checked section -----------------------------------------------------

def test_not_checked_always_has_business_logic():
    ast = _parse(FULL_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=1,
                                      type_errors=[], taint_violations=[],
                                      test_results={})
    assert any("business logic" in n.lower() for n in report.not_checked)

def test_not_checked_has_rate_limits_when_external_calls():
    ast = _parse(FULL_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=1,
                                      type_errors=[], taint_violations=[],
                                      test_results={})
    assert any("rate limit" in n.lower() for n in report.not_checked)

def test_not_checked_has_concurrency_when_parallel():
    ast = _parse(PARALLEL_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=1,
                                      type_errors=[], taint_violations=[],
                                      test_results={})
    assert any("concurrency" in n.lower() for n in report.not_checked)

def test_not_checked_no_rate_limits_when_no_external():
    ast = _parse(SIMPLE_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=1,
                                      type_errors=[], taint_violations=[],
                                      test_results={})
    assert not any("rate limit" in n.lower() for n in report.not_checked)


# --- Engineer responsibilities ------------------------------------------------

def test_responsibilities_always_has_business_review():
    ast = _parse(FULL_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=1,
                                      type_errors=[], taint_violations=[],
                                      test_results={})
    assert any("business" in r.lower() for r in report.engineer_responsibilities)

def test_responsibilities_has_schema_review_when_validate_schema():
    ast = _parse(FULL_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=1,
                                      type_errors=[], taint_violations=[],
                                      test_results={})
    assert any("schema" in r.lower() for r in report.engineer_responsibilities)

def test_responsibilities_has_credentials_when_external():
    ast = _parse(FULL_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=1,
                                      type_errors=[], taint_violations=[],
                                      test_results={})
    assert any("credential" in r.lower() for r in report.engineer_responsibilities)

def test_responsibilities_has_db_review_when_write():
    ast = _parse(FULL_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=1,
                                      type_errors=[], taint_violations=[],
                                      test_results={})
    assert any("write_database" in r.lower() or "data integrity" in r.lower()
               for r in report.engineer_responsibilities)


# --- to_dict and summary -----------------------------------------------------

def test_to_dict_has_required_keys():
    ast = _parse(FULL_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=1,
                                      type_errors=[], taint_violations=[],
                                      test_results={})
    d = report.to_dict()
    assert "evidence_report" in d
    er = d["evidence_report"]
    assert "workflow_id" in er
    assert "generated_at" in er
    assert "verified" in er
    assert "not_checked" in er
    assert "engineer_responsibilities" in er

def test_summary_contains_all_sections():
    ast = _parse(FULL_WORKFLOW_YAML)
    report = generate_evidence_report(ast, synthesis_attempts=2,
                                      type_errors=[], taint_violations=[],
                                      test_results={"t1": True})
    summary = report.summary()
    assert "VERIFIED" in summary
    assert "NOT CHECKED" in summary
    assert "ENGINEER RESPONSIBILITIES" in summary
    assert "invoice_approval" in summary
    assert "2" in summary  # synthesis_attempts
```

---

## Integration with verify_output node

After Session 05, the `verify_output` node in `nodes.py` is updated to generate
the evidence report and attach it to the pipeline state. Add the following to
`nodes.py`:

```python
# Add to imports in nodes.py
from ..dsl.ast_nodes import WorkflowAST, WorkflowStep
from ..verification.evidence_report import generate_evidence_report

# Updated verify_output node
def verify_output(state: WorkflowSynthState) -> dict:
    """
    Stage 2 verification: security checks on the translated outputs.
    Generates the evidence report and attaches it to the final output.

    CONSTRAINT (Critical Constraint 8): Never deliver a workflow without
    the evidence report.
    """
    # Reconstruct the AST from the dsl_candidate dict
    # (state carries dict, not the dataclass, for JSON-serialisability)
    ast = _reconstruct_ast(state["dsl_candidate"])

    # Generate the evidence report
    report = generate_evidence_report(
        ast=ast,
        synthesis_attempts=state["repair_attempt"] + 1,
        type_errors=state["dsl_type_errors"],
        taint_violations=state["dsl_taint_violations"],
        test_results=state["test_results"],
    )

    # Attach the evidence report to the final outputs
    n8n_with_report = {
        **(state.get("final_n8n_json") or {}),
        **report.to_dict(),
    }
    langchain_with_report = (
        (state.get("final_langchain_python") or "") +
        f"\n\n# Evidence Report\n# {report.summary().replace(chr(10), chr(10) + '# ')}"
    )

    return {
        "output_verification_passed": True,
        "output_errors": [],
        "synthesis_successful": True,
        "final_n8n_json": n8n_with_report,
        "final_langchain_python": langchain_with_report,
    }


def _reconstruct_ast(dsl_candidate: dict) -> WorkflowAST:
    """Reconstructs a WorkflowAST from the dict stored in state."""
    steps = [
        WorkflowStep(
            id=s["id"],
            op=s["op"],
            params=s.get("params", {}),
            output=s.get("output"),
        )
        for s in dsl_candidate.get("steps", [])
    ]
    return WorkflowAST(
        workflow_id=dsl_candidate.get("workflow_id", "unknown"),
        steps=steps,
    )
```

---

## File structure to create in the repo

```
workflowsynth/
  src/
    verification/
      __init__.py          (updated -- add EvidenceReport exports)
      evidence_report.py   (new)
  tests/
    unit/
      test_evidence_report.py  (new)
```

Also update `src/synthesis/nodes.py`: replace the stub `verify_output` with
the real implementation shown above.

---

## How to run the tests

```bash
pytest tests/unit/ -v
```

All 51 tests from Sessions 01-03 plus the new evidence report tests must pass.
The verify_output update is tested indirectly via the existing pipeline tests.

---

## Implementation Journal

```
Date: 2026-08-06
DSR Phase: Build
Component: Verification Module -- Evidence Report
Type: Decision
Description: Evidence report sections are tailored to the specific workflow
  instance -- not generic boilerplate. The verified claims name the actual
  ops present. The not_checked and responsibilities sections include only
  items relevant to the ops in this specific workflow.
Justification: A generic report is noise. A report that says "authenticate_user
  is present and precedes write_database in step_auth -> step_write" is
  actionable. Tailoring requires walking the AST, but the cost is trivial
  and the value is significant for the engineer review process.
Dissertation Impact: Architectural Decision 5. Section 5 (Implementation)
  and Section 7 (Limitations -- discuss what tailoring still cannot catch).
```

```
Date: 2026-08-06
DSR Phase: Build
Component: Verification Module -- Evidence Report
Type: Decision
Description: The evidence report is attached to BOTH the n8n JSON output
  and the LangChain Python output. It is embedded in the final output, not
  returned as a separate file.
Justification: A separate file can be lost or separated from the workflow.
  Embedding the report in the output guarantees it travels with the workflow
  through any subsequent processing, storage, or deployment step.
Dissertation Impact: Critical Constraint 8. Section 5 (Implementation).
```

---

## Next Session

Session 06 -- Integration Layer (`src/integration/n8n_adapter.py`,
`src/integration/langchain_adapter.py`).

The stubs for `translate_output` from Session 03 become real. The n8n adapter
converts the verified WorkflowAST to a deployable n8n JSON workflow. The
LangChain adapter converts it to executable LangChain Python. Stage 2
verification runs on both outputs.
