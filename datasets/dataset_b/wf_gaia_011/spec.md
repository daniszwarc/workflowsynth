# Workflow: Conditional Routing by Classification

## Context
Incoming items must be classified and then routed down one of two processing paths depending on the classification.

## Trigger
An item arrives that needs to be classified and routed.

## Steps
1. Fetch the item's details.
2. Classify the item using the classification rule.
3. Route the item to the appropriate processing path based on the classification.

## Constraints
- The routing decision must always be based on the freshly computed classification, never a cached one.
