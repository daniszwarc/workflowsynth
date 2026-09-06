# Workflow: Unpaid Invoice Alert Email

## Context
A scheduled alert emails the billing administrator a list of all unpaid invoices grouped by days overdue.

## Trigger
Scheduled internal alert run.

## Steps
1. Read all unpaid invoices with patient and due date information.
2. Authenticate the system service account.
3. Group invoices into overdue bands (1-30, 31-60, 61-90, 91-120, 121-150 days).
4. Format the alert as a summary with invoice counts per band.
5. Send the alert to the billing administrator.

## Constraints
- Alert is sent to internal billing administrator only -- not to patients.
- Invoices are grouped by the same 5 overdue bands used for late fees.
