# src/synthesis/prompts.py
#
# Prompt templates for WorkflowSynth LLM calls.
#
# Two prompts:
#   SYSTEM_PROMPT      -- the base system prompt for all LLM calls
#   build_repair_prompt -- builds a dynamic repair prompt from attempt errors
#
# The system prompt is the most critical component of the synthesis engine.
# Any change to it must be logged in the Implementation Journal and tested
# against a representative sample of Dataset A before committing.

SYSTEM_PROMPT = """You are WorkflowSynth, an AI system that generates enterprise workflow \
specifications in a formal YAML DSL.

Your task: given a natural language workflow description, generate a \
valid YAML workflow that uses ONLY the 25 approved DSL operations listed below.

## Output format

Respond with ONLY valid YAML. No explanation, no prose, no markdown code fences. \
The response must be parseable directly as YAML.

Required top-level fields:
  workflow_id: <snake_case identifier>
  steps: <list of steps>

Required per step:
  id: <unique snake_case identifier>
  op: <one of the 25 approved operations>

Optional per step:
  params: <dict of parameters>
  output: <variable name this step produces>

## The 25 approved operations

Data Operations:
  fetch_api         -- retrieve data from an external API endpoint
  filter_records    -- filter a dataset by condition
  transform_json    -- reshape or map JSON structure
  validate_schema   -- check data against a schema definition
  aggregate_data    -- group and summarise records
  merge_datasets    -- combine two datasets by key
  extract_field     -- pull a specific field from a record
  format_output     -- serialise data to a target format

Control Flow:
  route_to_step     -- conditional branching to a named step
  apply_rule        -- evaluate a business rule and return result
  loop_records      -- iterate over a collection
  parallel_execute  -- run two steps concurrently
  wait_for_condition -- pause until a condition is met
  handle_error      -- catch and route errors
  retry_step        -- retry a failed step N times
  terminate_workflow -- end execution with a status

Integration Operations:
  send_to_queue     -- publish a message to a queue
  log_audit         -- write an immutable audit log entry
  notify_user       -- send a notification to a user
  call_webhook      -- make an HTTP call to an external endpoint
  read_database     -- read records from a database table
  write_database    -- write records to a database table
  authenticate_user -- verify user identity and role
  encrypt_field     -- encrypt a sensitive data field
  call_subworkflow  -- invoke another workflow by ID

## Hard constraints

1. Use ONLY the 25 operations above. Any other op name is invalid.
2. Every step id must be unique within the workflow.
3. If a step references params.input, that variable must be declared \
as the output of a previous step.
4. Operations that require input (filter_records, transform_json, \
validate_schema, aggregate_data, merge_datasets, extract_field, \
format_output, write_database, send_to_queue, call_webhook, \
notify_user, encrypt_field) MUST declare params.input.
5. Any write_database or call_webhook step MUST be preceded by an \
authenticate_user step earlier in the workflow.
6. Data from fetch_api, read_database, call_webhook, or call_subworkflow \
is untrusted. It MUST pass through validate_schema, encrypt_field, \
transform_json, filter_records, or extract_field before reaching \
write_database, call_webhook, send_to_queue, notify_user, or log_audit.

## Example

workflow_id: invoice_approval_workflow
steps:
  - id: step_fetch_invoices
    op: fetch_api
    params:
      endpoint: "/api/invoices/pending"
    output: raw_invoices

  - id: step_validate
    op: validate_schema
    params:
      input: raw_invoices
      schema: invoice_schema
    output: validated_invoices

  - id: step_authenticate
    op: authenticate_user
    params:
      role: "approver"
    output: auth_result

  - id: step_write
    op: write_database
    params:
      input: validated_invoices
      table: approved_invoices
    output: write_result"""


def build_repair_prompt(
    original_spec: str,
    failing_yaml: str,
    type_errors: list[str],
    taint_violations: list[str],
    test_failures: dict,
    attempt_number: int,
    max_attempts: int,
) -> str:
    """
    Builds a repair prompt from the current attempt's errors.

    The repair prompt gives the LLM:
    - The original spec (so it never loses sight of the goal)
    - The failing YAML (so it knows what it produced)
    - The specific errors (so it knows exactly what to fix)
    - The attempt count (so it knows how many tries remain)

    Error messages from type_check() and taint_analysis() are already
    written to be useful in a repair prompt -- they reference the specific
    step, describe the problem, and suggest the fix.
    """
    parts = [
        f"Attempt {attempt_number + 1} of {max_attempts} failed.",
        "Generate a corrected YAML workflow that fixes ALL errors listed below.",
        "",
        "## Original specification",
        original_spec,
        "",
        f"## Your previous YAML (attempt {attempt_number})",
        failing_yaml,
        "",
    ]

    if type_errors:
        parts += [
            "## Type / structure errors to fix",
            *[f"- {e}" for e in type_errors],
            "",
        ]

    if taint_violations:
        parts += [
            "## Security violations to fix",
            *[f"- {v}" for v in taint_violations],
            "",
        ]

    if test_failures:
        failed = [k for k, v in test_failures.items() if not v]
        if failed:
            parts += [
                "## Failed tests",
                *[f"- {t}" for t in failed],
                "",
            ]

    parts += [
        "Respond with ONLY valid YAML. No prose, no markdown fences.",
    ]

    return "\n".join(parts)
