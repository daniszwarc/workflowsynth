# Workflow: Ticket Close and Archive

## Context
A producer closes a completed ticket and removes it from the active Kanban view. Archived tickets are retained in the database but hidden from the dashboard.

## Trigger
A producer clicks 'Close and Archive' in the ticket modal.

## Steps
1. Receive the close-and-archive request with the ticket ID.
2. Validate the request.
3. Update the ticket: status = cerrado, visible = false, closed_at = now().
4. Log the closure in ticket_history.

## Constraints
- visible = false hides the ticket from the Kanban dashboard.
- closed_at timestamp must be recorded.
