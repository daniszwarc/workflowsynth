# Workflow: Business Rule Validation

## Context
Extracted business rules must be human-verified before becoming searchable. A Validator, Editor, or Admin reviews and approves or rejects each rule.

## Trigger
A validator reviews an extracted rule.

## Steps
1. Receive the rule validation decision with the rule ID.
2. Authenticate the user and verify Validator, Editor, or Admin role.
3. Read the rule record and verify it is in pending_review status.
4. Update the rule status to approved or rejected.
5. Log the validation action in the audit trail.

## Constraints
- Only Validator, Editor, Admin, and Developer roles can validate rules.
- Rules must be in pending_review status.
- Every validation decision must be logged.
