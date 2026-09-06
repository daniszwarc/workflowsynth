# Workflow: Hybrid Knowledge Base Search

## Context
Users search the knowledge base using natural language. The search combines vector similarity with full-text search using Reciprocal Rank Fusion across business rules, reference articles, and SEDs.

## Trigger
An authenticated user submits a search query.

## Steps
1. Receive the search query from the authenticated user.
2. Authenticate the user.
3. Generate a query embedding.
4. Run vector similarity search across rules, articles, and seds tables.
5. Run full-text search across the same tables.
6. Apply Reciprocal Rank Fusion to merge and re-rank results.

## Constraints
- Only validated rules (status = approved) appear in search results.
- Both vector and full-text results are merged using Reciprocal Rank Fusion.
