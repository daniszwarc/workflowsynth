# Workflow: Complex Reasoning With Encrypted Storage

## Context
A batch of records must have multi-step rules applied in a loop, the results aggregated, a security check applied, and the outcome stored encrypted, with stakeholders notified and the run audited.

## Trigger
A batch reasoning job runs over a queued set of records.

## Steps
1. Fetch the batch of records to process.
2. Loop over each record in the batch.
3. Apply the multi-step reasoning rule to each record during the loop.
4. Transform the per-record rule outcomes into a collected-results format.
5. Aggregate the collected results from the loop.
6. Apply the security validation rule to the aggregated results.
7. Extract the sensitive fields flagged by the security validation.
8. Authenticate as the reasoning service before storing.
9. Encrypt the extracted sensitive fields.
10. Store the encrypted, aggregated results.
11. Notify stakeholders that the batch run completed.
12. Log the batch run for audit purposes.

## Constraints
- The security validation rule must be applied before the results are encrypted and stored.
