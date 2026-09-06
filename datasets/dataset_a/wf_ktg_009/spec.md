# Workflow: HR Calendar and Employee Administration

## Context
An internal HR module tracks calendar events, disciplinary records, and employee status for the company's own staff.

## Trigger
An HR staff member submits a calendar event, disciplinary record, or status change.

## Steps
1. Receive the HR action form.
2. Authenticate the HR staff user.
3. Look up the configuration type from the relevant lookup table.
4. Insert the HR record into the appropriate table.

## Constraints
- HR module is separate from claimant case management.
