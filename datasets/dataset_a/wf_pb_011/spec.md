# Workflow: Stalled Ticket Alert

## Context
The brokerage monitors open tickets for stalled work. Any ticket that has not changed status in more than 4 hours triggers an alert to the assigned producer.

## Trigger
Scheduled check during business hours.

## Steps
1. Read all open tickets not updated in the last 4 hours.
2. Filter to include only assigned tickets.
3. Aggregate stalled tickets by producer.
4. Format an alert notification for each stalled ticket group.
5. Send the alert to the assigned producer.
6. Log the alert in the audit trail.

## Constraints
- Only assigned tickets generate alerts.
- Each alert must be logged.
