# Workflow: WhatsApp Text Message Ingestion

## Context
An insurance brokerage receives client requests via WhatsApp. Each incoming text message must be parsed, sanitised of sensitive financial data, classified by an AI model to determine if it represents a work request, and if so, registered as a ticket.

## Trigger
A WhatsApp message webhook POST arrives from the messaging platform.

## Steps
1. Extract and normalise the message fields from the webhook payload.
2. Mask sensitive data in the message text (credit card numbers, DNI, CBU, alias).
3. Call the AI classification API to determine if the message is a work request.
4. If not a work request (es_laboral = false), terminate the workflow.
5. Look up the producer assigned to the recipient WhatsApp number.
6. Create or update the client record using the sender name.
7. Create a new ticket with the classification result.
8. Record the original message as the first entry in the ticket message log.

## Constraints
- Sensitive data must be masked BEFORE the text reaches the AI classification API.
- Only messages with es_laboral = true generate tickets.
