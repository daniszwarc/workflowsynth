# Workflow: Primary-Secondary API Enrichment

## Context
Data from a primary API must be enriched with additional fields from a secondary API, and the combined result validated.

## Trigger
A request arrives that requires enriching a primary record with secondary data.

## Steps
1. Fetch the primary record from the primary API.
2. Fetch enrichment data from the secondary API.
3. Merge the primary record with the enrichment data.
4. Validate the combined, enriched result.

## Constraints
- The combined result must be validated before it is returned to the caller.
