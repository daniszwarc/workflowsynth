# src/dsl/constants.py
#
# Official WorkflowSynth DSL vocabulary.
# These 25 operators are the only permitted vocabulary.
# No component may accept an op that is not listed here.
#
# CONSTRAINT: changing this vocabulary requires updating type_checker.py,
# taint.py, and all Dataset A test suites. Log it in the Implementation Journal.

# --- The 25 valid operators ---------------------------------------------------

VALID_OPS: set[str] = {
    # Data Operations (8)
    "fetch_api",
    "filter_records",
    "transform_json",
    "validate_schema",
    "aggregate_data",
    "merge_datasets",
    "extract_field",
    "format_output",

    # Control Flow (8)
    "route_to_step",
    "apply_rule",
    "loop_records",
    "parallel_execute",
    "wait_for_condition",
    "handle_error",
    "retry_step",
    "terminate_workflow",

    # Integration Operations (9)
    "send_to_queue",
    "log_audit",
    "notify_user",
    "call_webhook",
    "read_database",
    "write_database",
    "authenticate_user",
    "encrypt_field",
    "call_subworkflow",
}

# --- Output type signatures ---------------------------------------------------
#
# Each operator declares an output type.
# The type checker uses this to validate that the output of one step
# is compatible with the input of the step that consumes it.
#
# Possible types:
#   "records"    -- list of records (list of dicts)
#   "record"     -- a single record (dict)
#   "boolean"    -- True / False
#   "string"     -- text
#   "any"        -- flexible output (type checking is permissive)
#   "none"       -- no output produced (side-effect only)
#   "auth_token" -- result of authenticate_user; required before write ops

OP_OUTPUT_TYPES: dict[str, str] = {
    # Data Operations
    "fetch_api":       "records",
    "filter_records":  "records",
    "transform_json":  "records",
    "validate_schema": "records",
    "aggregate_data":  "record",
    "merge_datasets":  "records",
    "extract_field":   "any",
    "format_output":   "string",

    # Control Flow
    "route_to_step":      "none",
    "apply_rule":         "boolean",
    "loop_records":       "none",
    "parallel_execute":   "none",
    "wait_for_condition": "none",
    "handle_error":       "none",
    "retry_step":         "none",
    "terminate_workflow": "none",

    # Integration Operations
    "send_to_queue":     "none",
    "log_audit":         "none",
    "notify_user":       "none",
    "call_webhook":      "any",
    "read_database":     "records",
    "write_database":    "none",
    "authenticate_user": "auth_token",
    "encrypt_field":     "string",
    "call_subworkflow":  "any",
}

# --- Operators that require an input param ------------------------------------
#
# These operators must have params.input declared.
# The type checker verifies that the referenced input exists as the output
# of a previous step.

OPS_REQUIRING_INPUT: set[str] = {
    "filter_records",
    "transform_json",
    "validate_schema",
    "aggregate_data",
    "merge_datasets",
    "extract_field",
    "format_output",
    "write_database",
    "send_to_queue",
    "call_webhook",
    "notify_user",
    "encrypt_field",
}

# --- Security rule: authenticate_user must precede these ops -----------------
#
# CONSTRAINT (Architectural Decision 3):
# Any step using these operators must have a preceding authenticate_user step.
# This rule is enforced in the type checker, not the taint analyser.

OPS_REQUIRING_AUTH: set[str] = {
    "write_database",
    "call_webhook",
}
