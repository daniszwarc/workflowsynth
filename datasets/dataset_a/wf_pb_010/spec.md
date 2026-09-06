# Workflow: Client Record Upsert

## Context
Every time a message arrives from a client, the system ensures a client record exists. If the client is new, a record is created. If they already exist, the existing record is returned.

## Trigger
Called from ingestion workflows when a new message is received.

## Steps
1. Extract the client identifier from the incoming message.
2. Validate the identifier is not empty.
3. Check if a client record already exists with this identifier.
4. Upsert the client record.
5. Extract the client ID for use in ticket creation.

## Constraints
- Deduplication is by name for WhatsApp and by email for email ingestion.
