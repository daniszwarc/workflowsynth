# Workflow: Create Work Order

## Context
Technicians create work orders for repair jobs. The workflow applies weekday-based shipping cutoff logic and branches on whether the work order is linked to a product recall.

## Trigger
A technician submits a work order creation form.

## Steps
1. Receive the work order form with unit serial, technician, and service details.
2. Authenticate the submitting user.
3. Read the unit card and ERP vendor information.
4. Validate the unit card exists.
5. Apply the weekday shipping cutoff rule: Thursday or Friday flags delayed shipping.
6. Apply the recall linkage rule: if linked to a recall, insert the recall linkage record.
7. Insert the work order record.
8. Insert the labor rates record.

## Constraints
- Thursday/Friday flag affects shipping scheduling.
- Recall-linked work orders require a valid recall code.
- Labor rates must be recorded alongside the work order.
