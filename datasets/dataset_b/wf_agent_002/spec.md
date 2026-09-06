# Workflow: Database Summary Query

## Context
A summary of records in a table is needed for a quick status check.

## Trigger
A status-check request arrives asking for a table summary.

## Steps
1. Query the database table.
2. Aggregate the query results into a summary.

## Constraints
- The summary must reflect the current state of the table at query time.
