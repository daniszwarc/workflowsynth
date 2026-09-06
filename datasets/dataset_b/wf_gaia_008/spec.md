# Workflow: Rule-Based Record Update

## Context
Records read from a database must have a business rule applied before the result is written back.

## Trigger
A scheduled job triggers a pass over pending records.

## Steps
1. Read the pending records from the database.
2. Authenticate as the processing service before writing any changes.
3. Validate the pending records against the expected schema.
4. Apply the business rule to determine the outcome for each record.
5. Write the outcome back to the database.

## Constraints
- Records must never be written back without the rule having been applied first.
