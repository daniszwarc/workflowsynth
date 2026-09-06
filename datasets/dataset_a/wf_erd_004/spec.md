# Workflow: Timesheet Daily Entry

## Context
Field workers enter their daily worked hours and kilometres per patient through an AJAX-backed editable grid.

## Trigger
A field worker updates a cell in the timesheet grid.

## Steps
1. Receive the cell update with the composite key and new value.
2. Authenticate the submitting worker.
3. Parse the composite key to extract worker ID, patient ID, date, and entry type.
4. Validate the value.
5. Update the timesheet detail record.

## Constraints
- Composite key format: workerID_patientID_date_flag.
- Workers can only edit their own timesheet entries.
- Timesheet must be in status 1 (draft) to accept edits.
