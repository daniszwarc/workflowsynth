# Workflow: User Authentication and Session Initialization

## Context
A medical rehabilitation billing platform authenticates staff before granting access. Every request is gated by a session check. On successful login, a role-based session is established.

## Trigger
A staff member submits the login form.

## Steps
1. Intercept every incoming request and check if the session is authenticated.
2. If not authenticated and the request is not the login form, redirect to login.
3. Receive the login form submission with username and password.
4. Look up the user record and verify the password.
5. On success, establish a role-based session and redirect to the main menu.

## Constraints
- Session timeout: 8 hours of inactivity.
- Role assignment determines which menus and operations are visible.
