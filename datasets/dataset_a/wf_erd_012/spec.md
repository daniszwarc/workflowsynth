# Workflow: Worker Rate Change with Confirmation

## Context
Worker billing rates are changed through a two-step confirmation workflow to prevent silent errors that would cascade into invoices and payroll.

## Trigger
An admin submits a rate change request.

## Steps
1. Receive the rate change request with worker ID and new rate.
2. Authenticate the admin user.
3. Read the current worker rate to display on the confirmation page.
4. Apply the confirmation rule: present old and new rate for review.
5. On confirmation, update the worker rate record.

## Constraints
- Only admin role can change worker rates.
- Two-step confirmation is mandatory.
- Rate changes cascade into future invoices and payroll.
