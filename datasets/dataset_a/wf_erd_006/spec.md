# Workflow: Standard Invoice Creation

## Context
Office staff generate invoices from approved timesheet hours. The system computes applicable provincial sales taxes for taxable patients, assigns a sequential invoice number, and posts the total to the patient balance.

## Trigger
An office staff member initiates invoice creation for a patient and billing period.

## Steps
1. Receive the invoice creation request.
2. Authenticate the office staff user.
3. Read approved timesheet hours (status 3) for this patient and period.
4. Validate that approved hours exist.
5. Apply the tax computation rule for taxable patients.
6. Assign the next sequential invoice number.
7. Create the invoice header record.
8. Create invoice line item records.
9. Post the invoice total to the patient balance.

## Constraints
- Only approved timesheets (status 3) can be invoiced.
- Provincial sales taxes are applied only if patient.taxable = true.
- Invoice creation and balance update must both succeed.
