# Workflow: Worker Assignment to Patient

## Context
Therapists and home-care workers are assigned to specific patients. Assignments determine which timesheets and invoices are linked.

## Trigger
An office staff member submits an assignment request.

## Steps
1. Receive the assignment request with patient ID and worker ID.
2. Authenticate the submitting user.
3. Verify both the patient and worker records exist and are active.
4. Create the worker-patient assignment record.

## Constraints
- Assignment links the worker to the patient for timesheet and invoice generation.
