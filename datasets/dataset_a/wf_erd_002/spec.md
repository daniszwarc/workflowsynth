# Workflow: Patient Registration

## Context
Office staff register new patients referred for home-care or rehabilitation therapy. Patient records include insurance flags, taxable status, and billing language preference.

## Trigger
An office staff member submits a new patient registration form.

## Steps
1. Receive the new patient registration form.
2. Authenticate the submitting user.
3. Validate the patient record fields.
4. Check for duplicate patient records.
5. Store the new patient record.

## Constraints
- language field determines EN/FR invoice template selection.
- taxable field determines whether provincial sales taxes are applied.
