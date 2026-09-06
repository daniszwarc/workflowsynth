# Workflow: Full Email Ingestion Pipeline

## Context
Orchestrates the complete email ingestion flow: IMAP retrieval, normalisation, deduplication, AI classification, and ticket creation.

## Trigger
New unread emails arrive in the IMAP inbox.

## Steps
1. Read new unread emails from the IMAP inbox.
2. Normalise fields, fix encoding, strip quoted reply history.
3. Mask sensitive financial data in subject and body.
4. Extract the message ID for deduplication.
5. Check if message ID has already been processed.
6. If already processed, skip to the next email.
7. Register the message ID in the deduplication registry.
8. Call the AI classification API.
9. Parse the classification response with fallback defaults.
10. If not a work request, skip ticket creation.
11. Look up the producer from the recipient email address.
12. Create or update the client record.
13. Create the ticket with fuente = mail.
14. Record the email body in the ticket message log.
15. Write an audit log entry.

## Constraints
- Deduplication must occur BEFORE AI classification.
- Sensitive data must be masked before the AI API.
- Full audit trail required.
