# Workflow: E-Commerce Checkout

## Context
A shopper's cart must be validated, any promo code applied, the order processed, and the customer notified of the outcome.

## Trigger
A shopper initiates checkout for their cart.

## Steps
1. Fetch the shopper's cart contents.
2. Validate the cart contents against the checkout schema.
3. Apply the promo code rule, if one was supplied.
4. Authenticate the shopper before processing payment.
5. Process the order.
6. Notify the customer that their order was placed.

## Constraints
- The cart must be validated before any promo rule is applied.
- The order must never be processed without the shopper being authenticated.
