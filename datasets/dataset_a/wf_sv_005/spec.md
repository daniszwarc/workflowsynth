# Workflow: Non-Customer-Support Email Routing

## Context
When an incoming email is classified as not requiring customer support (internal emails, automated notifications), the workflow routes it away from the agent pipeline without creating a draft.

## Trigger
An email has been classified as customerSupport = false.

## Steps
1. Receive the classification result indicating customerSupport = false.
2. Apply the routing rule to confirm the email should be skipped.
3. Log the skipped email for audit purposes.

## Constraints
- Internal emails (@club.example.com) always route to this path.
- No draft is created and no response is generated.
