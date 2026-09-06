# Workflow: Full Email Support Pipeline

## Context
The complete end-to-end email support pipeline. Monitors the inbox, classifies incoming emails, and for customer support requests searches three knowledge bases and creates a Gmail draft in the customer's language. Internal emails are silently skipped. The agent never sends emails directly.

## Trigger
A new unread email arrives in the club Gmail inbox.

## Steps
1. Poll the Gmail inbox every 5 minutes for new unread emails.
2. Extract the email body, thread ID, and sender address.
3. Retrieve the full conversation thread for context.
4. Build the thread history, labelling each message by sender type.
5. Classify the email: customer support request or not.
6. Route: if not customer support, log and skip. If customer support, continue.
7. Search all three knowledge bases: customerSupportDocs, clubDocuments, previousEmailResponses.
8. Detect the email language (EN/FR/ES) and apply season mapping rules.
9. Generate a draft response using only knowledge base content.
10. Create a Gmail draft in the customer's language.
11. Log the draft creation in the audit trail.

## Constraints
- All three knowledge bases must be searched before drafting.
- The agent never sends email directly -- only creates drafts.
- Response language must match the customer (EN/FR/ES).
- Season mapping: Fall = Winter (Oct-Apr), Spring = Summer (May-Sep).
