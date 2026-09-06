# Workflow: Payment Application

## Context
Office staff record patient payments against specific invoices. The system determines whether the payment fully or partially covers the invoice amount.

## Trigger
An office staff member records a patient payment.

## Steps
1. Receive the payment record with patient ID, invoice ID, and payment amount.
2. Authenticate the office staff user.
3. Read the invoice to get the total amount and prior payments.
4. Apply the payment classification rule: full if total payments >= invoice amount.
5. Store the payment record.
6. Update the invoice status.
7. Update the patient running balance.

## Constraints
- Full payment: prior + new payments >= invoiceAmount.
- Payment and balance update must both succeed.
