# Workflow: Outbound Email Notification

## Context
A generic outbound email endpoint sends notifications triggered by other workflows -- intake errors, password resets, and manual notifications.

## Trigger
A workflow triggers an outbound email notification.

## Steps
1. Receive the email send request with recipient, subject, and body.
2. Authenticate the requesting service.
3. Send the email to the specified recipient.

## Constraints
- Used by intake error alerting and password recovery.
- Recipient is always an internal staff address.
