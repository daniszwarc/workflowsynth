# Workflow: Webhook Ingestion Pipeline

## Context
Incoming webhook payloads must be validated, reshaped, routed by type, stored, and confirmed back to the sender.

## Trigger
A webhook payload arrives from an external system.

## Steps
1. Fetch the incoming webhook payload.
2. Validate the payload against the webhook schema.
3. Transform the validated payload into the internal event format.
4. Route the event based on its type.
5. Authenticate as the ingestion service before storing.
6. Store the transformed event.
7. Confirm receipt back to the sender.

## Constraints
- A payload must be validated and transformed before it is ever stored.
