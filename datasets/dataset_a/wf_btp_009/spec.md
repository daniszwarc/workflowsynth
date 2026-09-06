# Workflow: Clinical Platform Audit Log Entry

## Context
Every administrative action on the clinical platform generates an immutable audit log entry. The audit log is append-only and visible only to admins.

## Trigger
Any administrative action is performed on the platform.

## Steps
1. Receive the action details from the triggering operation.
2. Authenticate that the logging request comes from an authorized internal service.
3. Write the immutable audit log entry with action, user, resource, and timestamp.

## Constraints
- Audit log is append-only -- entries are never updated or deleted.
- Every admin action must generate an audit log entry.
