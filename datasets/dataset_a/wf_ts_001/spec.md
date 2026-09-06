# Workflow: Timesheet Hours Entry

## Context
Staff and coaches log their worked hours per patient for a specific date and role. The system computes total pay, checks for overlapping entries, and inserts the record.

## Trigger
A staff member submits a timesheet entry form.

## Steps
1. Receive the timesheet entry form with user ID, date, hours, role, and rate.
2. Authenticate the submitting user.
3. Validate the entry date falls within the currently active date range.
4. Check for overlapping timesheet entries for this user/date/role.
5. Compute the total pay amount (hours multiplied by rate).
6. Insert the timesheet record.

## Constraints
- Entry date must fall within the active timesheet date range.
- Overlapping entries for the same user/date/role are rejected.
- Total pay = hours x rate -- computed at entry time.
