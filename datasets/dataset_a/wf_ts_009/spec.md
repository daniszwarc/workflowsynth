# Workflow: Bulk Email Broadcast

## Context
Administrators send bulk email announcements to all parents or all coaches registered in the system.

## Trigger
An admin submits a bulk email composition form.

## Steps
1. Receive the bulk email form with subject, body, and recipient group.
2. Authenticate the admin user.
3. Read all email addresses for the selected recipient group.
4. Filter to include only users with a valid email address.
5. Send the bulk email to all filtered recipients.

## Constraints
- Only admin role can send bulk emails.
- Recipient group must be selected: parents or coaches.
- Only users with a valid email receive the broadcast.
