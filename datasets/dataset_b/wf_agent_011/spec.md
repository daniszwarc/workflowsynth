# Workflow: Verified Database Migration

## Context
A migration task must read from the source, transform and validate the data, write it to the target, verify the write, and log the migration.

## Trigger
A migration job runs to move data from a source table to a target table.

## Steps
1. Read the source records to migrate.
2. Transform the source records into the target schema's format.
3. Validate the transformed records against the target schema.
4. Authenticate as the migration service before writing.
5. Write the validated records to the target table.
6. Read back the migrated records from the target table.
7. Verify the write by validating the migrated records once more.
8. Log the migration for audit purposes.

## Constraints
- The transformed records must pass validation both before and after the write.
