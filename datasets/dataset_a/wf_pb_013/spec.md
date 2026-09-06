# Workflow: Ticket Message Log Entry

## Context
Every incoming message associated with a ticket is stored in the messages table as a log entry linked to the ticket.

## Trigger
Called after ticket creation or update in any ingestion workflow.

## Steps
1. Extract ticket ID, producer ID, message source, and content from the ingestion context.
2. Validate that ticket ID and message content are present.
3. Sanitise the message content to remove any sensitive data.
4. Insert the message record into the messages table with direction = 'entrante'.
5. Log the message insertion in the audit trail.

## Constraints
- direction must always be 'entrante' for client messages.
- Sensitive data must be masked before storage.
