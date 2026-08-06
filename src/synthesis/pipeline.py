# src/synthesis/pipeline.py
#
# LangGraph graph definition for the WorkflowSynth synthesis pipeline.
# Defines nodes, edges, conditional routing, and compiles the graph.
#
# Usage:
#   from workflowsynth.synthesis.pipeline import build_pipeline, run_synthesis
#   pipeline = build_pipeline()
#   final_state = run_synthesis(pipeline, "When an invoice arrives, validate and store it.")

from langgraph.graph import StateGraph, END
from .state import WorkflowSynthState, initial_state
from .nodes import (
    translate_to_dsl,
    verify_dsl,
    run_tests,
    check_pass_or_repair,
    repair_with_llm,
    translate_output,
    verify_output,
    record_failure,
)


def build_pipeline():
    """
    Builds and compiles the LangGraph synthesis pipeline.

    Graph structure:
        START -> translate_to_dsl -> verify_dsl -> run_tests
             -> check_pass_or_repair (conditional)
                  "pass"           -> translate_output -> verify_output -> END
                  "repair"         -> repair_with_llm -> verify_dsl (loop)
                  "record_failure" -> record_failure -> END

    Returns a compiled LangGraph runnable.
    """
    graph = StateGraph(WorkflowSynthState)

    # Register nodes
    graph.add_node("translate_to_dsl", translate_to_dsl)
    graph.add_node("verify_dsl", verify_dsl)
    graph.add_node("run_tests", run_tests)
    graph.add_node("translate_output", translate_output)
    graph.add_node("verify_output", verify_output)
    graph.add_node("repair_with_llm", repair_with_llm)
    graph.add_node("record_failure", record_failure)

    # Entry point
    graph.set_entry_point("translate_to_dsl")

    # Linear edges
    graph.add_edge("translate_to_dsl", "verify_dsl")
    graph.add_edge("verify_dsl", "run_tests")
    graph.add_edge("translate_output", "verify_output")
    graph.add_edge("verify_output", END)
    graph.add_edge("record_failure", END)

    # Repair loop: repair_with_llm goes back to verify_dsl (not translate_to_dsl)
    # The spec does not change -- only the candidate changes on repair.
    graph.add_edge("repair_with_llm", "verify_dsl")

    # Conditional routing from run_tests via check_pass_or_repair
    graph.add_conditional_edges(
        "run_tests",
        check_pass_or_repair,
        {
            "pass": "translate_output",
            "repair": "repair_with_llm",
            "record_failure": "record_failure",
        }
    )

    return graph.compile()


def run_synthesis(pipeline, natural_language_spec: str) -> WorkflowSynthState:
    """
    Runs the full synthesis pipeline for a natural language spec.

    Args:
        pipeline: compiled LangGraph pipeline from build_pipeline()
        natural_language_spec: the workflow description in plain English

    Returns:
        The final WorkflowSynthState after the pipeline completes.
        Check state["synthesis_successful"] to determine outcome.
    """
    state = initial_state(natural_language_spec)
    return pipeline.invoke(state)
