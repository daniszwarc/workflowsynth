# Workflow: Employer and System Configuration Management

## Context
Administrators maintain system-wide and per-employer configuration lookup entries used across the system.

## Trigger
An admin submits a configuration create, update, or delete form.

## Steps
1. Receive the configuration form with type, value, and scope.
2. Authenticate the admin user.
3. Validate the configuration fields.
4. Insert, update, or delete the configuration record.

## Constraints
- Configuration entries are scoped to system-wide or per-employer context.
