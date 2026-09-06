# Workflow: Record Loop With Rule Collection

## Context
A batch of records must each have a business rule applied, with the results collected into a single output.

## Trigger
A batch job triggers processing of a queued set of records.

## Steps
1. Fetch the batch of queued records.
2. Loop over each record in the batch.
3. Apply the business rule to each record during the loop.
4. Transform each record's outcome into the collected-results format.
5. Aggregate the collected results from the loop into a summary.

## Constraints
- Every record in the batch must be visited exactly once.
