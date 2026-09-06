# Workflow: Knowledge Base Ranked Search

## Context
A query against the agent's knowledge base should return a ranked list of matching results.

## Trigger
A query arrives that needs to be matched against the knowledge base.

## Steps
1. Fetch candidate matches from the knowledge base.
2. Filter the candidates down to those above the relevance threshold.

## Constraints
- Only results above the relevance threshold should be returned, in ranked order.
