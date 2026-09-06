# Workflow: Embeddings Backfill Cron Job

## Context
A scheduled cron job runs every 15 minutes to detect and backfill any missing embeddings across rules, articles, and SEDs.

## Trigger
Scheduled -- every 15 minutes inside the wiki container.

## Steps
1. Trigger on schedule (every 15 minutes).
2. Read all rules, articles, and SEDs that have no corresponding embedding record.
3. Filter to only records missing embeddings.
4. For each record without embeddings, generate and store embeddings.

## Constraints
- Runs every 15 minutes automatically.
- AI cold start can take 2-3 minutes -- the job must handle this gracefully.
- Logs to /var/log/backfill.log.
