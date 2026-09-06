# Workflow: Claim and Claimant Intake

## Context
A workers' compensation case management system onboards new claimants. The intake is multi-tenant aware and writes to multiple tables in a single transaction, with a tickler follow-up automatically scheduled.

## Trigger
A case staff member submits a new claimant intake form.

## Steps
1. Receive the new claimant intake form from case staff.
2. Authenticate the submitting user.
3. Validate the required claimant fields.
4. Apply the tenant branching rule: select the correct field list based on the client database.
5. Compute the next claimant ID.
6. Insert the claimant record.
7. Insert the workers' comp case stub.
8. Insert placeholder ICD code rows.
9. Insert placeholder return-to-work rows.
10. Log a 'New Patient Set Up' activity and insert the default tickler follow-up.

## Constraints
- Tenant branching: field list varies by client database.
- Error handling: emails a full form dump to internal staff on failure.
- Default tickler follow-up is automatically inserted for all new claimants.
