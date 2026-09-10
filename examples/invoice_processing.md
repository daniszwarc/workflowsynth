# Workflow: Invoice Email Ingestion

## Context
A finance team receives supplier invoices as email attachments. Each incoming invoice must be parsed, validated against required fields, stored in the accounting database, and the accounting team notified so they can review it.

## Trigger
An email webhook POST arrives when a new message with an invoice attachment is received.

## Steps
1. Extract and normalise the invoice fields (supplier name, invoice number, amount, due date) from the email payload.
2. Validate that all required fields are present and correctly typed before proceeding.
3. If validation fails, terminate the workflow.
4. Authenticate against the accounting system.
5. Store the validated invoice record in the accounting database.
6. Notify the accounting team via a webhook call that a new invoice is ready for review.

## Constraints
- The invoice must pass field validation before it is written to the database.
- The accounting system must be authenticated before any database write.
- Only validated invoices trigger the accounting team notification.
