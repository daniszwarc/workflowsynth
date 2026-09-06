# Workflow: Add Recall Code

## Context
Administrators create recall codes that can be linked to work orders when a product recall is underway.

## Trigger
An admin submits a new recall code.

## Steps
1. Receive the recall code and description from the admin form.
2. Authenticate the admin user.
3. Insert the recall record into the recall master table.

## Constraints
- Only admin role can create recall codes.
- Recall codes are referenced by work orders when servicing recalled units.
