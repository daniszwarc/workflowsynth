# Workflow: Secured Multi-Source Data Pipeline

## Context
Sensitive data pulled from two sources must be authenticated, validated, encrypted, and only then persisted, with every step logged.

## Trigger
A scheduled pipeline run triggers ingestion from two sensitive sources.

## Steps
1. Authenticate as the pipeline service.
2. Fetch data from the first sensitive source.
3. Fetch data from the second sensitive source.
4. Merge the two datasets.
5. Validate the merged dataset against the sensitive-data schema.
6. Extract the sensitive fields from the validated dataset.
7. Encrypt the extracted sensitive fields.
8. Store the encrypted dataset.
9. Log the storage action for audit purposes.

## Constraints
- Data must be authenticated, validated, and encrypted, in that order, before it is ever persisted.
- Every persistence action must be recorded in the audit log.
