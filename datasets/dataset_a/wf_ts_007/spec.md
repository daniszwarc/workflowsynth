# Workflow: Internal Request and Approval

## Context
Staff submit internal requests. Admins approve or reject them, triggering an email notification.

## Trigger
A staff member submits a request or an admin changes a request status.

## Steps
1. Receive the request action with request ID and decision.
2. Authenticate the user.
3. Read the request record.
4. Update the request status.
5. Send an email notification to the requester.

## Constraints
- Any staff member can submit a request.
- Only admin can approve or reject.
- Email notification is sent on every status change.
