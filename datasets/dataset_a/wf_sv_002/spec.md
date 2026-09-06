# Workflow: Sent Email History Ingestion

## Context
The AI email agent improves its responses by learning from past email exchanges. Sent emails from the club Gmail account are retrieved, chunked, embedded, and indexed into the email history knowledge base.

## Trigger
Scheduled weekly to index the previous month's sent emails.

## Steps
1. Retrieve all sent emails from the past month, excluding the last 2 weeks.
2. Filter out emails with no body or very short bodies (under 20 characters).
3. For each email, build a structured text chunk combining subject, date, recipient, and body. Chunk into 500-character pieces with 50-character overlap.
4. Embed each chunk using the embedding model.
5. Insert all embedded chunks into the vector store email-history namespace.

## Constraints
- Chunking uses 500-char size with 50-char overlap to preserve context.
- Each chunk gets a unique ID: sent-{messageId}-chunk-{index}.
- Emails shorter than 20 characters are skipped.
