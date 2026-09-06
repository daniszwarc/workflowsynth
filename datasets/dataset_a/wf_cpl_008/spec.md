# Workflow: Request and Comment Moderation

## Context
A ticketing system allows users to submit requests about sports content. Admins review submissions. Two email notifications are triggered: on creation and on status change.

## Trigger
A user submits a request or an admin changes a request status.

## Steps
1. Receive the request submission form.
2. Validate the submission fields.
3. Insert the request with status 'pending'.
4. Send a creation notification email to the admin.
5. When an admin reviews and sets a new status, receive the status update.
6. Authenticate the admin user.
7. Update the request status.
8. Send a status notification email to the requester.

## Constraints
- Requests start in 'pending' status.
- Two email notifications: on creation (to admin) and on status change (to requester).
- No authentication required to submit a request.
