# Workflow: PET-SUV Data Extraction with Cache

## Context
PET-CT imaging reports contain SUVmax values for lesions that must be extracted and structured for the clinical dashboard. Results are cached for 24 hours to avoid redundant LLM calls.

## Trigger
A user loads the PET-SUV dashboard view.

## Steps
1. Receive the PET-SUV data request.
2. Authenticate the requesting user.
3. Check the 24-hour cache for existing PET-SUV data.
4. If cache is valid and no force-refresh, return cached data.
5. If cache is stale, read all PET imaging documents from the raw store.
6. Call the LLM to extract structured SUVmax values, lesion locations, and dates.

## Constraints
- Cache TTL: 24 hours. X-Force-Refresh header bypasses the cache.
- Only imaging documents of type PET are included.
- LLM extraction must not infer -- only extract values explicitly stated.
