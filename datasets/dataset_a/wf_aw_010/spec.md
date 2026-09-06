# Workflow: User Management

## Context
Administrators manage user accounts. The five-tier role system (Viewer, Validator, Editor, Admin, Developer) enforces SOX-compliant access controls.

## Trigger
An admin creates, updates, or deactivates a user account.

## Steps
1. Receive the user management request with user details and role assignment.
2. Authenticate the requesting user and verify Admin role.
3. Validate the user details and role assignment.
4. Apply the user management operation: create, update, or deactivate.
5. Log the user management action in the audit trail.

## Constraints
- Only Admin and Developer roles can manage users.
- Valid roles: Viewer, Validator, Editor, Admin, Developer.
- Every user management action must be logged.
