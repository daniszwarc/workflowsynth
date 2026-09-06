# Workflow: Finalize Unit History Transfer

## Context
When a unit serial number is corrected, repair history is transferred from the old serial to the corrected one.

## Trigger
An admin confirms a history transfer between serial numbers.

## Steps
1. Receive the transfer request with source and destination serial numbers.
2. Authenticate the admin user.
3. Delete the history records for the source serial number and redirect to the destination unit card.

## Constraints
- Only admin role can perform history transfers.
- The operation is irreversible -- source history records are permanently deleted.
- A confirmation step is required before the delete is executed.
