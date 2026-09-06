# Workflow: Daily Ticket Summary Email

## Context
An insurance brokerage sends each producer a daily summary of their open tickets every weekday. Tickets stalled for more than 4 hours are flagged with a warning.

## Trigger
Scheduled -- weekdays at 11:00 AM.

## Steps
1. Read all open tickets from the database, excluding closed and archived records.
2. Group tickets by producer and calculate hours without a status update.
3. Format a summary email per producer with warning flags on stalled tickets.
4. Send the formatted summary email to each producer.

## Constraints
- Only open tickets (status != cerrado) and visible tickets (visible = true) are included.
- Tickets stalled more than 4 hours must be flagged.
