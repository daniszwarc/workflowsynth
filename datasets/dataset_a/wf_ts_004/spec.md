# Workflow: Active Timesheet Date Range Configuration

## Context
The admin sets the active date range for timesheet entries. Only entries within this range are accepted.

## Trigger
An admin submits a new date range configuration.

## Steps
1. Receive the date range configuration form.
2. Authenticate the admin user.
3. Update the active date range in the timesheet_dates table.

## Constraints
- Only admin role can change the active date range.
- Start date must be before or equal to end date.
