# Workflow: Order Fulfillment Routing

## Context
A confirmed order must be checked against inventory, routed to the correct fulfillment path, and the supplier and audit trail updated.

## Trigger
An order is confirmed and ready for fulfillment.

## Steps
1. Fetch the confirmed order details.
2. Validate the order against the fulfillment schema.
3. Check current inventory availability for the order's items.
4. Validate the inventory status data before it is used for routing.
5. Route the order to the in-stock or backorder fulfillment path based on availability.
6. Notify the supplier when the order is routed to the backorder path.
7. Log the fulfillment routing decision for audit purposes.

## Constraints
- The routing decision must be based on a fresh inventory check, not a cached value.
- Every fulfillment decision must be logged.
