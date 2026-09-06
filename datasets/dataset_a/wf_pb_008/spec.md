# Workflow: Ticket Status Change

## Context
A producer moves a ticket between status columns on the Kanban dashboard. Every status change is automatically logged in the ticket history.

## Trigger
A producer changes a ticket's status via the dashboard.

## Steps
1. Receive the status update request with the ticket ID and new status.
2. Validate the new status (must be one of: pendiente, en_proceso, cerrado).
3. Update the ticket record with the new status.
4. Log the transition in ticket_history.

## Constraints
- Status must be one of: pendiente, en_proceso, cerrado.
- Every change must be logged in ticket_history.
