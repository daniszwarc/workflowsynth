# Workflow: Knowledge Base Top Result Search

## Context
A user wants the single best-matching answer from an internal knowledge base for a free-text query.

## Trigger
A search query arrives from a user-facing search box.

## Steps
1. Search the knowledge base for the query.
2. Extract the top-ranked result from the search results.

## Constraints
- Only the single best result should be returned to the caller.
