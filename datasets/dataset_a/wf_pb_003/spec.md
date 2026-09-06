# Workflow: Email Message Ingestion

## Context
An insurance brokerage monitors a producer's email inbox for client requests. Each incoming email must be normalised, deduplicated by message ID, sanitised, classified by AI, and if actionable, registered as a ticket.

## Trigger
A new unread email arrives in the producer's IMAP inbox.

## Steps
1. Retrieve the new unread email from the IMAP inbox.
2. Normalise email fields: fix encoding, extract addresses, strip quoted reply history.
3. Mask sensitive financial data in subject and body.
4. Check if this message ID has already been processed (deduplication).
5. If already processed, skip and continue to the next email.
6. Register the message ID to prevent future duplicates.
7. Call the AI classification API to extract structured fields.
8. If not a work request, skip ticket creation.
9. Look up the producer from the recipient email address.
10. Create or update the client record.
11. Create a new ticket with all extracted classification fields.
12. Record the email body as the first message in the ticket log.

## Constraints
- Deduplication must occur BEFORE classification to avoid redundant AI calls.
- Sensitive data must be masked before reaching the AI API.
- Only es_laboral = true emails generate tickets.
