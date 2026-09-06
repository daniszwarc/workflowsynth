# Workflow: User Authentication and Session

## Context
Staff log into the timesheet system using username and password. Login events are logged.

## Trigger
A staff member submits the login form.

## Steps
1. Receive the login form with username and password.
2. Look up the user record and verify credentials.
3. Apply the rate limit rule.
4. If remember-me is selected, apply the extended session rule.
5. Establish the user session with their role.
6. Log the login event in the audit table.

## Constraints
- Login events must be logged.
- Remember-me extends the session beyond the browser session.
