# Workflow: Staff Record Management

## Context
Admins create and update staff and coach records including hourly rate and pay_status.

## Trigger
An admin submits a staff record create or update form.

## Steps
1. Receive the staff record form.
2. Authenticate the admin user.
3. Validate the staff record fields.
4. Apply the pay_status rule: validate status is AUT or SPD.
5. Create or update the staff record.

## Constraints
- Only admin role can create or modify staff records.
- pay_status must be AUT (authorized) or SPD (processed).
