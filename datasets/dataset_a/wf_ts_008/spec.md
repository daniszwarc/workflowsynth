# Workflow: Forgot Password Email

## Context
Users who forgot their password can request credentials sent to their registered email.

## Trigger
A user submits a forgot password request.

## Steps
1. Receive the forgot password request with the user's email.
2. Look up the user record by email address.
3. Apply the account exists rule: if not found, return generic response.
4. Send the credentials email to the registered address.

## Constraints
- Credentials are sent only to the email address on file.
- If no account found, response does not reveal whether email exists.
