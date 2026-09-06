# Workflow: Case Tickler and Follow-Up Management

## Context
Case managers schedule, update, and complete follow-up reminders (ticklers) on active claims. Ticklers are the core diary mechanism for tracking next actions.

## Trigger
A case manager creates, updates, or completes a tickler from a claim record.

## Steps
1. Receive the tickler create, update, or complete request.
2. Authenticate the case manager.
3. Validate the tickler fields.
4. Insert or update the tickler record using a UUID primary key.
5. Log the tickler action.

## Constraints
- Tickler uses UUID as primary key -- no race condition on insert.
- Database transaction with rollback protects data integrity.
- Tickler is assigned to a specific case manager.
