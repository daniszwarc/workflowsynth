# Workflow: Manual Ticket Creation

## Context
A producer manually creates a ticket from the dashboard when a client request arrives through a channel not covered by automated ingestion.

## Trigger
A producer submits the manual ticket creation form on the dashboard.

## Steps
1. Receive the manual ticket creation request from the dashboard API.
2. Validate the request fields (required: tipo; optional: client name, notes).
3. Create or update the client record.
4. Create the ticket with status 'pendiente' and source 'manual'.

## Constraints
- tipo must be one of: alta, baja, a_definir.
