# Workflow: Database Read-Transform-Write

## Context
Records read from one table must be transformed and the result written to another table.

## Trigger
A scheduled job triggers a read-transform-write pass.

## Steps
1. Read the source records from the database.
2. Transform the records into the target format.
3. Authenticate as the migration service before writing.
4. Write the transformed records to the target table.

## Constraints
- Records must be transformed before they are written to the target table.
