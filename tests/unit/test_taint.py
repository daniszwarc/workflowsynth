# tests/unit/test_taint.py
#
# Unit tests for the taint analysis engine.
# Each test covers a specific data flow scenario.

import pytest
from workflowsynth.dsl.parser import parse_workflow
from workflowsynth.verification.taint import taint_analysis, TaintViolation


def _parse(yaml_string: str):
    """Helper: parses YAML and returns the AST. Asserts parsing succeeds."""
    result = parse_workflow(yaml_string)
    assert result["ok"] is True, f"Parser failed: {result.get('errors')}"
    return result["ast"]


# --- No violations (safe workflows) -----------------------------------------

def test_clean_workflow_no_sources():
    """A workflow with no sources has no tainted data -- no violations."""
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: authenticate_user
    params:
      role: admin
  - id: s2
    op: write_database
    params:
      table: logs
"""
    ast = _parse(yaml)
    assert taint_analysis(ast) == []


def test_source_sanitised_before_sink():
    """fetch_api -> validate_schema -> write_database: taint removed. No violation."""
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: fetch_api
    params:
      endpoint: "/invoices"
    output: raw_data
  - id: s2
    op: validate_schema
    params:
      input: raw_data
      schema: invoice_schema
    output: clean_data
  - id: s3
    op: authenticate_user
    params:
      role: admin
  - id: s4
    op: write_database
    params:
      input: clean_data
      table: invoices
"""
    ast = _parse(yaml)
    assert taint_analysis(ast) == []


def test_source_encrypted_before_sink():
    """fetch_api -> encrypt_field -> write_database: encrypted = sanitised. No violation."""
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: fetch_api
    output: raw
  - id: s2
    op: encrypt_field
    params:
      input: raw
    output: encrypted
  - id: s3
    op: authenticate_user
    params:
      role: admin
  - id: s4
    op: write_database
    params:
      input: encrypted
      table: secure_table
"""
    ast = _parse(yaml)
    assert taint_analysis(ast) == []


def test_read_database_sanitised_before_webhook():
    """read_database -> transform_json -> call_webhook: taint removed. No violation."""
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: read_database
    params:
      table: orders
    output: raw_orders
  - id: s2
    op: transform_json
    params:
      input: raw_orders
    output: transformed
  - id: s3
    op: authenticate_user
    params:
      role: system
  - id: s4
    op: call_webhook
    params:
      input: transformed
      url: "https://partner.example.com/orders"
"""
    ast = _parse(yaml)
    assert taint_analysis(ast) == []


def test_filter_records_as_sanitiser():
    """filter_records is a valid sanitiser -- removes taint."""
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: fetch_api
    output: raw
  - id: s2
    op: filter_records
    params:
      input: raw
    output: filtered
  - id: s3
    op: authenticate_user
    params:
      role: admin
  - id: s4
    op: write_database
    params:
      input: filtered
      table: t
"""
    ast = _parse(yaml)
    assert taint_analysis(ast) == []


# --- Violations (unsafe workflows) ------------------------------------------

def test_fetch_direct_to_write_database():
    """
    fetch_api -> write_database with no sanitiser.
    Classic taint violation: unsanitised external data written to DB.
    """
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: fetch_api
    params:
      endpoint: "/data"
    output: raw_data
  - id: s2
    op: authenticate_user
    params:
      role: admin
  - id: s3
    op: write_database
    params:
      input: raw_data
      table: my_table
"""
    ast = _parse(yaml)
    violations = taint_analysis(ast)
    assert len(violations) == 1
    assert violations[0].step_id == "s3"
    assert violations[0].op == "write_database"
    assert violations[0].tainted_var == "raw_data"
    assert violations[0].taint_origin == "s1"


def test_read_database_direct_to_send_to_queue():
    """read_database -> send_to_queue with no sanitiser. Violation."""
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: read_database
    params:
      table: users
    output: user_data
  - id: s2
    op: send_to_queue
    params:
      input: user_data
      queue: outbound
"""
    ast = _parse(yaml)
    violations = taint_analysis(ast)
    assert len(violations) == 1
    assert violations[0].tainted_var == "user_data"


def test_taint_propagates_through_neutral_op():
    """
    fetch_api -> aggregate_data (neutral) -> write_database.
    Taint propagates through aggregate_data (not a sanitiser).
    Violation at write_database.
    """
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: fetch_api
    output: raw
  - id: s2
    op: aggregate_data
    params:
      input: raw
    output: aggregated
  - id: s3
    op: authenticate_user
    params:
      role: admin
  - id: s4
    op: write_database
    params:
      input: aggregated
      table: t
"""
    ast = _parse(yaml)
    violations = taint_analysis(ast)
    assert len(violations) == 1
    assert violations[0].tainted_var == "aggregated"
    # Taint origin is still s1 (where taint was introduced)
    assert violations[0].taint_origin == "s1"


def test_multiple_violations_in_one_workflow():
    """
    Two sinks receiving tainted data. Both violations reported in one pass.
    """
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: fetch_api
    output: raw
  - id: s2
    op: notify_user
    params:
      input: raw
  - id: s3
    op: send_to_queue
    params:
      input: raw
"""
    ast = _parse(yaml)
    violations = taint_analysis(ast)
    assert len(violations) == 2
    ops = {v.op for v in violations}
    assert "notify_user" in ops
    assert "send_to_queue" in ops


def test_taint_stops_after_sanitiser():
    """
    fetch_api -> validate_schema -> aggregate_data -> write_database.
    validate_schema removes taint. aggregate_data operates on clean data.
    write_database receives clean data. No violation.
    """
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: fetch_api
    output: raw
  - id: s2
    op: validate_schema
    params:
      input: raw
      schema: s
    output: clean
  - id: s3
    op: aggregate_data
    params:
      input: clean
    output: summary
  - id: s4
    op: authenticate_user
    params:
      role: admin
  - id: s5
    op: write_database
    params:
      input: summary
      table: t
"""
    ast = _parse(yaml)
    assert taint_analysis(ast) == []


def test_call_webhook_as_source_then_sink():
    """
    call_webhook output is tainted (it is a source).
    A second call_webhook receiving that tainted output is a violation.
    """
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: call_webhook
    params:
      url: "https://partner.example.com/data"
    output: partner_data
  - id: s2
    op: authenticate_user
    params:
      role: system
  - id: s3
    op: call_webhook
    params:
      input: partner_data
      url: "https://internal.example.com/ingest"
"""
    ast = _parse(yaml)
    violations = taint_analysis(ast)
    assert len(violations) == 1
    assert violations[0].tainted_var == "partner_data"


def test_no_taint_without_output():
    """
    A source step with no declared output produces no named tainted variable.
    No taint to propagate.
    """
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: fetch_api
    params:
      endpoint: "/ping"
  - id: s2
    op: authenticate_user
    params:
      role: admin
  - id: s3
    op: write_database
    params:
      table: logs
"""
    ast = _parse(yaml)
    # s1 has no output -- no tainted variable introduced
    # s3 has no input -- not checking any variable
    assert taint_analysis(ast) == []
