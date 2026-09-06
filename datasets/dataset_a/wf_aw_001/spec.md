# Workflow: User Login with Two-Factor Authentication

## Context
A SOX-compliant internal knowledge base authenticates employees. Login requires email and password followed by a second factor -- TOTP or email code. Sessions expire after 8 hours.

## Trigger
An employee submits the login form.

## Steps
1. Receive the login form submission with email and password.
2. Validate the credentials against the users table.
3. Apply the rate limit rule: reject if more than 10 login attempts per IP in the last minute.
4. Determine the user's 2FA method (TOTP or email code).
5. For email 2FA: generate and send a verification code via email.
6. Validate the 2FA code. Apply rate limit: 5 attempts per 5 minutes per token.
7. Create an 8-hour session and log the login event.

## Constraints
- Rate limits: 10 attempts/min on login (per IP), 5 attempts/5min on 2FA (per token).
- Sessions stored as httpOnly Secure cookies, expire after 8 hours.
- Every login event must be logged in the audit trail.
