# Workflow: Close Work Order History Status

## Context
When a repair case is resolved, the work order history status is closed. This removes the active-lock record and updates the history status to Closed.

## Trigger
A user closes a resolved repair case.

## Steps
1. Receive the close status request with history ID.
2. Authenticate the user.
3. Remove the active-lock record from activeHistory.
4. Insert a follow-up counter record marking the close date.
5. Update the history record status to Closed.

## Constraints
- activeHistory record must be removed to release the in-progress lock.
- Close date is recorded in followUpCounter for reporting.
