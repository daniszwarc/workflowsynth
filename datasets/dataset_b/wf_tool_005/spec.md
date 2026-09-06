# Workflow: Validated API Data Storage

## Context
Data pulled from an API must pass schema validation before it is stored.

## Trigger
A sync job triggers a pull of data that must be validated before storage.

## Steps
1. Fetch the data from the API.
2. Validate the data against the expected schema.
3. Authenticate as the storage service before writing.
4. Store the validated result.

## Constraints
- Data failing validation must never reach storage.
