# Workflow: Authenticated Paginated Aggregation

## Context
An authenticated API must be queried for paginated results, which are then aggregated into a single summary.

## Trigger
A reporting job requests an aggregated summary from a paginated API.

## Steps
1. Authenticate against the paginated API.
2. Fetch the paginated data.
3. Aggregate the paginated data into a single summary.

## Constraints
- The API must never be queried without prior authentication.
