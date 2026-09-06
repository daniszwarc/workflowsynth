# Workflow: Timesheet Hours Edit

## Context
Existing timesheet entries can be edited. The same overlap check applies, excluding the record being edited.

## Trigger
A staff member submits an edit to an existing timesheet entry.

## Steps
1. Receive the edit form with the existing record ID and updated fields.
2. Authenticate the submitting user.
3. Read the existing timesheet record.
4. Check for overlapping entries, excluding the record being edited.
5. Update the timesheet record with new values and recomputed pay amount.

## Constraints
- Overlap check excludes the record being edited.
- Total pay is recomputed from updated hours and rate on every edit.
