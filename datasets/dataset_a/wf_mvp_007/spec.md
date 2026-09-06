# Workflow: Approve Invoice and Upload Payment

## Context
Administrators approve work order invoices. The approval writes to two separate databases for migration compatibility and handles an optional PDF invoice upload.

## Trigger
An admin approves a work order invoice.

## Steps
1. Receive the invoice approval request with work order ID and payment details.
2. Authenticate the admin user.
3. Validate the payment amount and work order ID.
4. Insert the payment record into the legacy payments table.
5. Insert the payment record into the new service payments table.
6. If a PDF invoice was uploaded, validate it and store it.
7. Update the work order history status to approved.
8. Log the approval in the audit trail.

## Constraints
- Dual-datasource write: both legacy and new service databases must be updated.
- PDF upload must be validated as application/pdf before storage.
- Only admin role can approve invoices.
