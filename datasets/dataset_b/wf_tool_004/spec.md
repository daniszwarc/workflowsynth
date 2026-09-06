# Workflow: Two-API Chain With Transformation

## Context
Data must be fetched from a first API, reshaped, and then used to query a second API.

## Trigger
A request arrives that needs data enriched by chaining two APIs.

## Steps
1. Fetch the initial data from the first API.
2. Transform the initial data into the format expected by the second API.
3. Query the second API with the transformed data.

## Constraints
- The second API must only ever be queried with transformed, not raw, data.
