# Workflow: Currency Conversion Logging

## Context
A caller wants a currency conversion result, with the conversion recorded for auditing purposes.

## Trigger
A request arrives with a source amount, source currency, and target currency.

## Steps
1. Call the currency conversion API with the requested amounts.
2. Extract the converted amount from the API response.
3. Log the conversion result for audit purposes.

## Constraints
- Every conversion must be logged, regardless of the amount involved.
