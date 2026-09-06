# Workflow: Insurance-Specific Invoice Creation

## Context
Patients referred through the provincial auto insurance board require invoices in a specific format. The workflow applies insurer-specific line item formatting and submission rules.

## Trigger
An office staff member initiates an insurance-specific invoice for a referred patient.

## Steps
1. Receive the invoice request with patient ID, insurer dossier number, and billing period.
2. Authenticate the office staff user.
3. Read approved timesheet hours for this patient and period.
4. Validate that the patient has a valid insurer dossier number.
5. Apply insurer-specific billing rules and format line items.
6. Create the insurer-specific invoice header.
7. Create insurer-specific line items.
8. Post the invoice total to the patient balance.

## Constraints
- Insurance invoices do not apply provincial sales taxes.
- Patient must have a valid insurer dossier number.
- Invoice format differs from standard -- separate templates apply.
