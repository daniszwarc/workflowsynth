# Workflow: Full E-Commerce Pipeline

## Context
A complete shopping journey: search for a product, authenticate the shopper, validate and process the order, fulfill it, notify the customer, and record the audit trail.

## Trigger
A shopper completes a purchase from search through fulfillment.

## Steps
1. Search the product catalog for the requested item.
2. Authenticate the shopper.
3. Validate the shopper's cart against the checkout schema.
4. Process the validated order.
5. Fulfill the order by delegating to the fulfillment subworkflow.
6. Extract the fulfillment status from the subworkflow's result.
7. Notify the customer that the order was fulfilled.
8. Log the completed purchase for audit purposes.

## Constraints
- The shopper must be authenticated before the order is processed.
- The completed purchase must always be logged for audit.
