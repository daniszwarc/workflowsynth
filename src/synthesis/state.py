# src/synthesis/state.py
#
# WorkflowSynthState: the single state object carried through the LangGraph pipeline.
# Every node reads from and writes to this object.
#
# CONSTRAINT: natural_language_spec is immutable after initialisation.
# CONSTRAINT: attempt_history is append-only. Never overwrite existing records.
# CONSTRAINT: max_attempts is always 10. Never change this value.

from typing import TypedDict, Optional


class WorkflowSynthState(TypedDict):

    # Input -- immutable after initialisation
    natural_language_spec: str

    # Synthesis -- current attempt
    llm_sketch: str                     # raw YAML string from LLM
    dsl_candidate: dict                 # parsed AST as dict (None if parse failed)

    # Verification -- Stage 1 (DSL level)
    dsl_verification_passed: bool
    dsl_type_errors: list[str]
    dsl_taint_violations: list[str]

    # Verification -- Stage 2 (output level)
    output_verification_passed: bool
    output_errors: list[str]

    # Loop control
    repair_attempt: int                 # 0 on first attempt; increments on each failure
    max_attempts: int                   # Always 10 -- the pass@10 definition

    # Per-attempt history -- append-only, never overwritten
    # Each record: attempt_number, llm_sketch, type_errors, taint_violations,
    #              test_results, failure_category
    attempt_history: list[dict]

    # Test execution results
    test_results: dict                  # test_id -> True (pass) / False (fail)

    # Final outputs (None until synthesis succeeds)
    final_n8n_json: Optional[dict]
    final_langchain_python: Optional[str]
    synthesis_successful: bool

    # Failure taxonomy (populated by record_failure node)
    failure_reason: Optional[str]
    failure_category: Optional[str]


def initial_state(natural_language_spec: str) -> WorkflowSynthState:
    """
    Creates a fresh WorkflowSynthState for a new synthesis run.
    This is the only place where natural_language_spec is set.
    """
    return WorkflowSynthState(
        natural_language_spec=natural_language_spec,
        llm_sketch="",
        dsl_candidate={},
        dsl_verification_passed=False,
        dsl_type_errors=[],
        dsl_taint_violations=[],
        output_verification_passed=False,
        output_errors=[],
        repair_attempt=0,
        max_attempts=10,
        attempt_history=[],
        test_results={},
        final_n8n_json=None,
        final_langchain_python=None,
        synthesis_successful=False,
        failure_reason=None,
        failure_category=None,
    )
