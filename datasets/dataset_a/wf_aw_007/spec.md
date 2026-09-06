# Workflow: SED Streaming Search with AI Synthesis

## Context
The SED search endpoint streams results progressively. Per-SED summaries stream immediately, then an AI-generated synthesis streams as the final result.

## Trigger
An authenticated user submits a SED search query.

## Steps
1. Receive the SED search query.
2. Authenticate the user.
3. Generate a query embedding and search the seds table.
4. For each matching SED, stream a per-SED summary as an NDJSON chunk.
5. After all individual results are streamed, call the LLM to generate a synthesis.
6. Stream the synthesis as the final NDJSON chunk.
7. Log the search in the audit trail.

## Constraints
- Results stream progressively via NDJSON -- users see results immediately.
- The synthesis streams last, after all individual results.
