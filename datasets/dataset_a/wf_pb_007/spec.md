# Workflow: Duplicate Ticket Merge

## Context
When a new message arrives about an existing request, the system detects it as a potential duplicate. This workflow handles the merge path.

## Trigger
A producer clicks the merge action on a duplicate ticket card.

## Steps
1. Receive the merge request with the new ticket ID and the target ticket ID.
2. Read the duplicate ticket record.
3. Read the target ticket record.
4. Extract the message content from the duplicate ticket.
5. Append the message to the target ticket's message log.
6. Update the target ticket's resumen if the new message adds information.
7. Archive the duplicate ticket (visible = false).
8. Log the merge action in the target ticket's history.

## Constraints
- The duplicate ticket must be archived, not deleted.
- The merge must be logged in ticket_history.
