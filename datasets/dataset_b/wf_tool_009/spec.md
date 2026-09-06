# Workflow: Parallel API Fan-Out With Merge

## Context
Three independent endpoints must be called concurrently and their results merged into one dataset.

## Trigger
A request arrives that benefits from calling three endpoints concurrently.

## Steps
1. Execute calls to the three endpoints in parallel.
2. Fetch the result from the first endpoint.
3. Fetch the result from the second endpoint.
4. Fetch the result from the third endpoint.
5. Merge the three parallel results into one dataset.

## Constraints
- All three endpoints must be called before the merge step runs.
