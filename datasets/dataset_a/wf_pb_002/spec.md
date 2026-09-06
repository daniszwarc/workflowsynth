# Workflow: WhatsApp Audio Message Ingestion

## Context
An insurance brokerage receives voice messages from clients via WhatsApp. Audio messages must be downloaded, transcribed to text, sanitised, and processed through the AI classification pipeline.

## Trigger
A WhatsApp webhook POST arrives containing an audio message.

## Steps
1. Extract message fields from the webhook payload, identifying it as audio type.
2. Retrieve the audio file binary from the messaging platform API.
3. Send the audio binary to the transcription API to convert speech to text.
4. Mask sensitive data in the transcribed text.
5. Call the AI classification API to determine if the message is a work request.
6. If not a work request, terminate the workflow.
7. Look up the producer assigned to the recipient number.
8. Create or update the client record.
9. Create a new ticket with the classification result.
10. Record the transcribed message in the ticket message log.

## Constraints
- Audio must be transcribed BEFORE classification.
- Sensitive data must be masked before the text reaches the AI API.
- Only messages with es_laboral = true generate tickets.
