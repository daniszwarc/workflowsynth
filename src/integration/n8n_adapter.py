# src/integration/n8n_adapter.py
#
# Translates a verified WorkflowAST to an n8n-compatible JSON workflow.
#
# n8n is a visual workflow automation platform. Workflows are JSON objects
# containing nodes (operations) and connections (data flow between nodes).
# Each WorkflowAST step maps to one n8n node.
#
# The evidence report is embedded in the workflow metadata so it cannot
# be separated from the workflow during deployment (Critical Constraint 8).
#
# Usage:
#   from workflowsynth.integration.n8n_adapter import to_n8n_json
#   n8n_workflow = to_n8n_json(ast, evidence_report)

import json
from ..dsl.ast_nodes import WorkflowAST, WorkflowStep
from ..verification.evidence_report import EvidenceReport


# --- n8n node type mapping ---------------------------------------------------
#
# Maps each DSL op to the closest n8n node type.
# This is a best-effort mapping -- some DSL ops do not have a perfect
# n8n equivalent and use a generic node type.
# The deploying engineer is responsible for reviewing and adjusting
# node parameters for their specific environment (documented in the
# evidence report engineer_responsibilities section).

N8N_NODE_TYPES: dict[str, str] = {
    # Data Operations
    "fetch_api":       "n8n-nodes-base.httpRequest",
    "filter_records":  "n8n-nodes-base.filter",
    "transform_json":  "n8n-nodes-base.set",
    "validate_schema": "n8n-nodes-base.itemLists",
    "aggregate_data":  "n8n-nodes-base.summarize",
    "merge_datasets":  "n8n-nodes-base.merge",
    "extract_field":   "n8n-nodes-base.set",
    "format_output":   "n8n-nodes-base.set",

    # Control Flow
    "route_to_step":      "n8n-nodes-base.switch",
    "apply_rule":         "n8n-nodes-base.if",
    "loop_records":       "n8n-nodes-base.splitInBatches",
    "parallel_execute":   "n8n-nodes-base.splitInBatches",
    "wait_for_condition": "n8n-nodes-base.wait",
    "handle_error":       "n8n-nodes-base.stopAndError",
    "retry_step":         "n8n-nodes-base.httpRequest",
    "terminate_workflow": "n8n-nodes-base.noOp",

    # Integration Operations
    "send_to_queue":     "n8n-nodes-base.rabbitmq",
    "log_audit":         "n8n-nodes-base.set",
    "notify_user":       "n8n-nodes-base.emailSend",
    "call_webhook":      "n8n-nodes-base.httpRequest",
    "read_database":     "n8n-nodes-base.postgres",
    "write_database":    "n8n-nodes-base.postgres",
    "authenticate_user": "n8n-nodes-base.httpRequest",
    "encrypt_field":     "n8n-nodes-base.crypto",
    "call_subworkflow":  "n8n-nodes-base.executeWorkflow",
}

# Grid layout constants for the n8n visual editor
NODE_WIDTH = 240
NODE_HEIGHT = 100
NODE_SPACING_X = 300
NODE_START_X = 100
NODE_START_Y = 200


def to_n8n_json(ast: WorkflowAST, evidence_report: EvidenceReport) -> dict:
    """
    Translates a verified WorkflowAST to an n8n workflow JSON object.

    The output is a valid n8n workflow that can be imported directly
    into an n8n instance via Settings -> Import Workflow.

    The evidence report is embedded in workflow.meta so it travels
    with the workflow through any export/import cycle.

    Args:
        ast:            The verified WorkflowAST.
        evidence_report: The evidence report from generate_evidence_report().

    Returns:
        Dict representing the n8n workflow JSON.
    """
    nodes = []
    connections = {}

    for i, step in enumerate(ast.steps):
        node = _step_to_n8n_node(step, i)
        nodes.append(node)

        # Build connections: each node connects to the next
        # (linear flow -- parallel_execute and route_to_step
        # would need manual adjustment in the n8n editor)
        if i < len(ast.steps) - 1:
            next_step = ast.steps[i + 1]
            connections[step.id] = {
                "main": [[{"node": next_step.id, "type": "main", "index": 0}]]
            }

    return {
        "name": ast.workflow_id,
        "nodes": nodes,
        "connections": connections,
        "active": False,   # always False -- engineer must review before activating
        "settings": {
            "executionOrder": "v1",
        },
        "meta": {
            "workflowsynth_version": "1.0",
            "workflow_id": ast.workflow_id,
            "evidence_report": evidence_report.to_dict()["evidence_report"],
        },
        "tags": ["workflowsynth", "auto-generated"],
    }


def _step_to_n8n_node(step: WorkflowStep, index: int) -> dict:
    """
    Converts a single WorkflowStep to an n8n node dict.

    Position is calculated on a grid layout for the visual editor.
    Parameters are carried over from the DSL step -- the deploying
    engineer will need to map DSL params to n8n node parameters.
    """
    node_type = N8N_NODE_TYPES.get(step.op, "n8n-nodes-base.noOp")

    return {
        "id": step.id,
        "name": step.id,
        "type": node_type,
        "typeVersion": 1,
        "position": [
            NODE_START_X + index * NODE_SPACING_X,
            NODE_START_Y,
        ],
        "parameters": {
            **step.params,
            "_dsl_op": step.op,
            "_dsl_output": step.output,
        },
        "notes": (
            f"WorkflowSynth DSL op: {step.op}. "
            f"Review and configure parameters for your n8n environment."
        ),
    }


def to_n8n_json_string(ast: WorkflowAST, evidence_report: EvidenceReport) -> str:
    """Returns the n8n workflow as a formatted JSON string."""
    return json.dumps(to_n8n_json(ast, evidence_report), indent=2)
