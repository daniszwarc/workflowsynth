# Workflow: Secured API Aggregation Pipeline

## Context
Data aggregated from multiple APIs must be authenticated, encrypted, and only then persisted, satisfying a strict security constraint.

## Trigger
A scheduled job aggregates data from multiple APIs under a strict security policy.

## Steps
1. Authenticate as the aggregation service.
2. Fetch data from the first API.
3. Fetch data from the second API.
4. Aggregate the two datasets into a single result.
5. Extract the sensitive fields from the aggregated result.
6. Encrypt the extracted sensitive fields.
7. Store the encrypted, aggregated result.

## Constraints
- The aggregation service must authenticate before any data is fetched.
- The aggregated result must be encrypted before it is persisted.
