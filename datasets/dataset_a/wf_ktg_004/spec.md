# Workflow: User Account Creation and Password Recovery

## Context
Administrators create system user accounts with role assignments. Case manager users get an additional lookup record.

## Trigger
An admin submits a user creation form.

## Steps
1. Receive the user creation form with username, password, role, and case manager flag.
2. Authenticate the admin user.
3. Hash the password using the password hashing service.
4. Insert the employee record.
5. Insert the user record with role assignment.
6. Apply the case manager rule: if flagged, insert into the case manager lookup.

## Constraints
- Role is set at creation and stored in session at login.
- Password must be hashed before storage.
