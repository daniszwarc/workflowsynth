# tests/unit/test_type_checker.py

import pytest
from workflowsynth.dsl.parser import parse_workflow
from workflowsynth.dsl.type_checker import type_check


def _parse_and_check(yaml_string: str) -> list[str]:
    """Helper: parses YAML and runs the type checker. Returns errors."""
    result = parse_workflow(yaml_string)
    assert result["ok"] is True, f"Parser failed unexpectedly: {result.get('errors')}"
    return type_check(result["ast"])


# --- Valid workflows ---------------------------------------------------------

def test_valid_type_flow():
    """fetch_api -> validate_schema: records -> records. Should pass."""
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: fetch_api
    params:
      endpoint: "/data"
    output: raw_data
  - id: s2
    op: validate_schema
    params:
      input: raw_data
      schema: my_schema
    output: clean_data
  - id: s3
    op: authenticate_user
    params:
      role: admin
  - id: s4
    op: write_database
    params:
      input: clean_data
      table: my_table
"""
    errors = _parse_and_check(yaml)
    assert errors == []


# --- Input errors ------------------------------------------------------------

def test_missing_input_param():
    """validate_schema without params.input should fail."""
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: fetch_api
    output: data
  - id: s2
    op: validate_schema
    params:
      schema: my_schema
"""
    errors = _parse_and_check(yaml)
    assert any("missing required param 'input'" in e for e in errors)


def test_input_references_undefined_var():
    """Referencing an output that does not exist should fail."""
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: filter_records
    params:
      input: nonexistent_var
"""
    errors = _parse_and_check(yaml)
    assert any("not defined" in e for e in errors)


def test_input_references_later_step():
    """Cannot reference the output of a step that comes after."""
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: filter_records
    params:
      input: data_from_s2
  - id: s2
    op: fetch_api
    output: data_from_s2
"""
    errors = _parse_and_check(yaml)
    assert any("not defined" in e for e in errors)


# --- Type mismatch errors ----------------------------------------------------

def test_type_mismatch_string_into_records_op():
    """
    encrypt_field outputs 'string'.
    filter_records requires 'records'.
    Should produce a type error.
    """
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
    output: encrypted_value
  - id: s3
    op: filter_records
    params:
      input: encrypted_value
"""
    errors = _parse_and_check(yaml)
    assert any("type" in e.lower() for e in errors)


# --- Authentication rule errors ----------------------------------------------

def test_write_database_without_auth():
    """write_database without a preceding authenticate_user should fail."""
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: fetch_api
    output: data
  - id: s2
    op: write_database
    params:
      input: data
      table: t
"""
    errors = _parse_and_check(yaml)
    assert any("authenticate_user" in e for e in errors)
    assert any("write_database" in e for e in errors)


def test_call_webhook_without_auth():
    """call_webhook without a preceding authenticate_user should fail."""
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: fetch_api
    output: data
  - id: s2
    op: call_webhook
    params:
      input: data
      url: "https://example.com"
"""
    errors = _parse_and_check(yaml)
    assert any("authenticate_user" in e for e in errors)


def test_write_database_with_auth_passes():
    """write_database with a preceding authenticate_user should pass."""
    yaml = """
workflow_id: t
steps:
  - id: s1
    op: fetch_api
    output: data
  - id: s2
    op: authenticate_user
    params:
      role: admin
  - id: s3
    op: write_database
    params:
      input: data
      table: my_table
"""
    errors = _parse_and_check(yaml)
    auth_errors = [e for e in errors if "authenticate_user" in e]
    assert auth_errors == []
