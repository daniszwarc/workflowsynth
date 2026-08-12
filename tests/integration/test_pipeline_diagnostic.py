# tests/integration/test_pipeline_diagnostic.py
#
# Diagnostic integration test: runs the full pipeline and prints the
# complete final state for research inspection. No assertions beyond
# synthesis_successful -- the goal is visibility, not validation.
#
# REQUIRES: ANTHROPIC_API_KEY in .env
#
# Run with: pytest tests/integration/test_pipeline_diagnostic.py -v -s

import os
import json
import pytest
from dotenv import load_dotenv

load_dotenv()

pytestmark = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set -- skipping integration tests"
)

from workflowsynth.synthesis.pipeline import build_pipeline, run_synthesis

SPECS = {
    "simple_invoice": """
Workflow: Invoice Approval

When a batch of invoices arrives from the external billing API, validate
each invoice against the invoice schema, authenticate the approver, and
store the validated invoices in the database.
""",
    "security_patient": """
Workflow: Patient Data Ingestion

Read patient records from the external health API, validate the records
against the patient schema, authenticate the data engineer, and store
the validated records in the patient database.
""",
}


def _print_state(spec_name: str, state: dict):
    sep = "=" * 60
    print(f"\n{sep}")
    print(f"SPEC: {spec_name}")
    print(sep)
    print(f"synthesis_successful : {state['synthesis_successful']}")
    print(f"repair_attempt       : {state['repair_attempt']}")
    print(f"dsl_verification_passed : {state['dsl_verification_passed']}")
    print(f"dsl_type_errors      : {state['dsl_type_errors']}")
    print(f"dsl_taint_violations : {state['dsl_taint_violations']}")
    print(f"failure_category     : {state['failure_category']}")
    print(f"failure_reason       : {state['failure_reason']}")
    print()
    print("--- llm_sketch (last attempt) ---")
    print(state['llm_sketch'])
    print()
    print("--- dsl_candidate ---")
    print(json.dumps(state['dsl_candidate'], indent=2))
    print()
    print("--- test_results ---")
    print(json.dumps(state['test_results'], indent=2))
    print()
    print("--- attempt_history ---")
    if not state['attempt_history']:
        print("  (empty -- succeeded on first attempt)")
    else:
        for record in state['attempt_history']:
            print(f"  Attempt {record['attempt_number']}:")
            print(f"    failure_category : {record['failure_category']}")
            print(f"    type_errors      : {record['dsl_type_errors']}")
            print(f"    taint_violations : {record['dsl_taint_violations']}")
            print(f"    yaml_sketch      :")
            for line in record['llm_sketch'].splitlines():
                print(f"      {line}")
    print(sep)


@pytest.mark.parametrize("spec_name,spec", SPECS.items())
def test_pipeline_diagnostic(spec_name, spec):
    """
    Diagnostic test: runs the full pipeline and prints complete state.
    No assertions beyond synthesis_successful.
    Use -s flag to see full output: pytest tests/integration/test_pipeline_diagnostic.py -v -s
    """
    pipeline = build_pipeline()
    state = run_synthesis(pipeline, spec)
    _print_state(spec_name, state)
    assert state["synthesis_successful"] is True, (
        f"Synthesis failed for '{spec_name}' after {state['repair_attempt']} attempts. "
        f"See printed state above for details."
    )
