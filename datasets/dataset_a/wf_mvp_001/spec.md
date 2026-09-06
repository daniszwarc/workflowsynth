# Workflow: User Authentication and Session Bootstrap

## Context
A warranty and repair management system authenticates staff before granting access. Every request is gated by a session check. On successful login, a role-based session is established.

## Trigger
A staff member requests any page in the admin area.

## Steps
1. Intercept every incoming request and check if the session is authenticated.
2. If not authenticated, redirect to the login form.
3. Receive the login form submission with username and password.
4. Look up the user record and verify credentials.
5. Establish a role-based session and redirect to the main menu.

## Constraints
- Session timeout: 8 hours of inactivity.
- Role determines which menus and operations are visible.
