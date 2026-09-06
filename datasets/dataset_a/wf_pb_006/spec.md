# Workflow: Ticket Producer Assignment

## Context
When automated ingestion cannot determine which producer a ticket belongs to, it lands in the 'A confirmar' column unassigned. A manager assigns it manually from the dashboard.

## Trigger
A manager selects a producer from the assignment dropdown on an unassigned ticket card.

## Steps
1. Receive the assignment request with the ticket ID and selected producer ID.
2. Validate that the ticket exists and is currently unassigned.
3. Read the selected producer record to confirm they are active.
4. Update the ticket: set assigned_to and change status to 'pendiente'.
5. Log the status change in ticket history.
6. Notify the assigned producer that a new ticket has been assigned.

## Constraints
- Only unassigned tickets (assigned_to IS NULL) can be assigned via this workflow.
- Status change must be logged in ticket_history.
