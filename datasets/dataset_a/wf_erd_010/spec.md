# Workflow: Late Fee Computation and Application

## Context
Unpaid invoices past their due date accrue late fees at 2% per month in 30-day bands.

## Trigger
An admin runs the late fee computation.

## Steps
1. Read all unpaid invoices past their due date.
2. Authenticate the admin user.
3. For each unpaid invoice, compute the number of days overdue.
4. Apply the late fee tier rule: 2%/month in 30-day bands.
5. Compute the late fee amount.
6. Post the late fee to the patient balance.

## Constraints
- Due date: 23rd of the month following the billing month.
- Late fee rate: 2% per month, applied in 30-day bands.
- Only invoiceStatus = 1 (unpaid) invoices accrue late fees.
