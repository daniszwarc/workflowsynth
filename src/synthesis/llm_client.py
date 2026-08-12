# src/synthesis/llm_client.py
#
# LangChain LLM client factory for WorkflowSynth.
# Returns the appropriate LangChain chat model for a given attempt number.
#
# CONSTRAINT (Critical Constraint 6): Only Claude Opus 4.7 and GPT-5.4
# are approved providers. Do not introduce local models or other providers.
#
# Usage:
#   from workflowsynth.synthesis.llm_client import get_llm
#   llm = get_llm(attempt=0)
#   response = llm.invoke([HumanMessage(content="...")])

import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

load_dotenv()


def get_llm(attempt: int):
    """
    Returns the LangChain chat model for the given attempt number.

    Attempts 0-7: Claude Opus 4.7 (primary)
    Attempts 8-9: GPT-5.4 (fallback)

    The fallback strategy is deliberate: if Claude has failed 8 times,
    a different model architecture may find a solution Claude cannot.
    Both providers are accessed via LangChain -- swapping providers
    requires no changes to the node code.
    """
    if attempt <= 7:
        return _get_claude()
    return _get_gpt()


def _get_claude() -> ChatAnthropic:
    """Returns a Claude Opus 4.7 LangChain client."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY not set. "
            "Copy .env.example to .env and add your key."
        )
    return ChatAnthropic(
        model="claude-opus-4-6",
        api_key=api_key,
        max_tokens=2048,
        temperature=0.2,   # low temperature for deterministic DSL generation
    )


def _get_gpt() -> ChatOpenAI:
    """Returns a GPT-5.4 LangChain client."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY not set. "
            "Copy .env.example to .env and add your key."
        )
    return ChatOpenAI(
        model="gpt-5.4-2026-03-05",
        api_key=api_key,
        max_tokens=2048,
        temperature=0.2,
    )
