# Workflow: Filtered API Notification

## Context
Records fetched from an API must be filtered down to relevant ones, and a notification sent about them.

## Trigger
A monitoring job calls an API to check for new relevant records.

## Steps
1. Call the API to fetch the latest records.
2. Filter the records down to the relevant subset.
3. Send a notification about the relevant records.

## Constraints
- The notification must only ever describe the filtered, relevant records -- not the raw set.
