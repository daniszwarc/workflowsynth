# Workflow: Low-Stock Inventory Alert

## Context
A product's stock level must be checked against a threshold, and a notification sent if it has run low.

## Trigger
A scheduled inventory check triggers for a given product.

## Steps
1. Fetch the current stock level for the product.
2. Validate the stock data against the inventory schema.
3. Apply the low-stock threshold rule to the stock level.
4. Notify the inventory team if the stock has fallen below the threshold.

## Constraints
- A notification must only be sent when the threshold rule flags the product as low stock.
