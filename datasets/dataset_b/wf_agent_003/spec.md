# Workflow: Knowledge Graph Node Field Extraction

## Context
A specific node in a knowledge graph needs to have a subset of its fields returned.

## Trigger
A request arrives for specific fields of a named knowledge graph node.

## Steps
1. Fetch the knowledge graph node.
2. Extract the requested fields from the node.

## Constraints
- Only the requested fields should be returned, not the full node payload.
