# Workflow: Full WhatsApp Ingestion Pipeline

## Context
Orchestrates the complete WhatsApp processing pipeline from webhook receipt to ticket creation, handling both text and audio message types.

## Trigger
A WhatsApp message webhook POST arrives.

## Steps
1. Receive and parse the webhook payload.
2. Validate the message structure and block known spam numbers.
3. Normalise the recipient phone number.
4. Route by message type: text to sanitisation, audio to transcription.
5. For audio: retrieve file from platform API and transcribe.
6. Mask sensitive financial data in the message text.
7. Call the AI classification API.
8. If not a work request, terminate.
9. Look up the producer by recipient phone number.
10. Create or update the client record.
11. Create the ticket with all extracted fields.
12. Record the message in the ticket log.
13. Write an audit log entry.

## Constraints
- Audio must be transcribed before classification.
- Sensitive data must be masked before the AI classification API.
- Full audit trail required.
