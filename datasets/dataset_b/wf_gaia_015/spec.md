# Workflow: Full Reasoning and Audit Pipeline

## Context
A complete reasoning pipeline: gather data, classify it, route it, reshape it, verify the outcome, persist it, alert stakeholders, and record the full audit trail.

## Trigger
A high-value request arrives requiring the full reasoning pipeline.

## Steps
1. Fetch the source data for the request.
2. Classify the source data using the classification rule.
3. Route the request down the correct processing path based on the classification.
4. Transform the routed data into the canonical output format.
5. Validate the transformed data as a verification step before persisting.
6. Authenticate as the pipeline service before writing.
7. Store the verified, transformed result.
8. Notify the stakeholder that the pipeline has completed.
9. Log the entire pipeline run for audit purposes.

## Constraints
- The verification (validation) step must occur after transformation and before storage.
- Every completed run must be both notified and logged.
