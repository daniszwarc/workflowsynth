# Workflow: Timesheet Submission and Approval

## Context
Worker timesheets move through a three-status workflow: draft, submitted, and approved. Only approved timesheets can be used for invoice generation.

## Trigger
A worker submits or a supervisor approves a timesheet.

## Steps
1. Receive the submission or approval request with timesheet ID and action.
2. Authenticate the user and verify role for the action.
3. Read the current timesheet and verify the status transition is valid.
4. Apply the transition rule.
5. Update the timesheet status.
6. Write an audit note recording the transition.
7. Log the status change.

## Constraints
- Workers can only submit their own timesheets.
- Only approved timesheets (status 3) can generate invoices.
- Every status change must be logged.
