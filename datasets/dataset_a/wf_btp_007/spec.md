# Workflow: Liquid Biopsy Molecular Matrix Extraction

## Context
Liquid biopsy reports contain molecular profiling data that must be extracted and structured into a matrix for the clinical dashboard. The extraction uses an LLM and is cached for 24 hours.

## Trigger
A user loads the liquid biopsy dashboard view.

## Steps
1. Receive the liquid biopsy data request.
2. Authenticate the requesting user.
3. Check the 24-hour cache for existing liquid biopsy matrix data.
4. If cache is stale or force-refresh, read all liquid biopsy documents from the raw store.
5. Call the LLM to extract the molecular matrix: SNV/INDEL mutations, CNV alterations.
6. Format the results as a structured matrix for dashboard display.

## Constraints
- Cache TTL: 24 hours. X-Force-Refresh bypasses the cache.
- LLM must not infer -- only extract values explicitly stated.
