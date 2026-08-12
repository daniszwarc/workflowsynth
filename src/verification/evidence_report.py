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
