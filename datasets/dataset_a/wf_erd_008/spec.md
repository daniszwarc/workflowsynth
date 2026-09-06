# Workflow: Invoice Batch Email Generation

## Context
At billing cycle end, office staff trigger a batch email that sends PDF invoices to all patients who opted for email delivery in their preferred language.

## Trigger
An admin triggers batch invoice emailing for a billing period.

## Steps
1. Receive the batch email request with billing month and year.
2. Authenticate the admin user.
3. Read all invoices for this period where email delivery is enabled.
4. For each patient, generate a PDF invoice using the language-appropriate template.
5. Encrypt the PDF before attaching.
6. Send the invoice PDF to the patient's email address.
7. Log each email send in the audit trail.

## Constraints
- Only patients with email delivery enabled and a valid email address receive batch emails.
- Language selection is driven by patient.language field (EN or FR).
