# Workflow: Audited Database Update

## Context
A database update must read the current state, validate the requested change, transform it into the storage format, write it, and log the change.

## Trigger
An update request arrives for a specific database record.

## Steps
1. Read the current record from the database.
2. Validate the requested change against the update schema.
3. Transform the validated change into the storage format.
4. Authenticate as the update service before writing.
5. Write the transformed change to the database.
6. Log the update for audit purposes.

## Constraints
- Every write to the database must be preceded by validation and followed by an audit log entry.
