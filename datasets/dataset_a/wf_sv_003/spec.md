# Workflow: Incoming Email Classification

## Context
The email agent monitors the club inbox every 5 minutes. When a new unread email arrives, the full thread is retrieved and classified by an AI model to determine if it requires a customer support response.

## Trigger
A new unread email arrives in the club Gmail inbox.

## Steps
1. Poll the Gmail inbox every 5 minutes for new unread emails.
2. Extract the email body, thread ID, and sender address from the trigger payload.
3. Retrieve the full conversation thread using the thread ID.
4. Build the thread history: label each message as 'Club' or 'Customer' based on sender domain.
5. Call the AI classification API to determine if the email requires a customer support response.

## Constraints
- Emails from @club.example.com addresses are always classified as customerSupport = false.
- Classification covers EN/FR/ES -- the club operates multilingually in Montreal.
- Tax receipt requests (Releve 24, RL-24) are always classified as true.
