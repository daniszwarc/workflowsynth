# Workflow: Multi-API Orchestration With Retry

## Context
A multi-API operation must retry transient failures and route around persistent ones rather than failing outright.

## Trigger
A request triggers a multi-API operation that may encounter transient failures.

## Steps
1. Call the primary API for the operation.
2. Retry the call if it fails transiently.
3. Handle any error that persists after retries.
4. Route the operation to the fallback path if the error handler flags it as unrecoverable.

## Constraints
- Retries must be attempted before the operation is treated as failed.
