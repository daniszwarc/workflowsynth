# Workflow: Admin Authentication and Session

## Context
Admins log into the sports news admin panel. Every request is gated by a session check.

## Trigger
An admin requests any page in the admin area.

## Steps
1. Intercept every request and check if the session is authenticated.
2. If not authenticated, redirect to the login form.
3. Receive the login form submission.
4. Look up the user record and verify credentials.
5. Establish a session with the user's role and redirect to the admin menu.

## Constraints
- Every request is gated by the Application.cfm session check.
- Session role is stored but access control is enforced at the application level.
