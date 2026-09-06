# Workflow: Three-API Chain With Merge

## Context
Three related APIs must each be called, and their results merged and reshaped into one combined result.

## Trigger
A request arrives that requires combining data from three related APIs.

## Steps
1. Call the first API.
2. Call the second API.
3. Call the third API.
4. Merge the three results into a combined dataset.
5. Transform the combined dataset into the final output format.

## Constraints
- The transformation step must operate on the merged dataset, not any single API's raw result.
