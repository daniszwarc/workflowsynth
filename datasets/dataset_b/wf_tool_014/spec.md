# Workflow: Real-Time Classified Data Pipeline

## Context
Real-time data must be ingested, validated, transformed, classified, routed accordingly, stored, and the whole run audited.

## Trigger
A real-time data feed pushes a new event into the pipeline.

## Steps
1. Ingest the incoming real-time event.
2. Validate the event against the real-time schema.
3. Transform the validated event into the internal representation.
4. Classify the transformed event to determine its routing category.
5. Route the event based on its classification.
6. Authenticate as the pipeline writer before storing.
7. Store the classified event.
8. Log the pipeline run for audit purposes.

## Constraints
- Classification must occur after transformation and before routing.
- Every stored event must be logged in the audit trail.
