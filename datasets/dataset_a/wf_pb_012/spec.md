# Workflow: Email Deduplication Check

## Context
The email ingestion system processes multiple emails per cycle. Each email must be checked against a deduplication registry using its message ID.

## Trigger
Called for each email during the ingestion loop.

## Steps
1. Extract the message ID from the normalised email record.
2. Look up the message ID in the processed emails registry.
3. Apply the deduplication rule.
4. If duplicate, route to terminate. If new, route to registration.
5. Register the message ID with the current timestamp.
6. Return the confirmed-new email for downstream processing.

## Constraints
- message_id is the deduplication key.
- Registration must happen before classification.
