# Workflow: Stock Price Lookup and Logging

## Context
An analyst wants the latest price of a given stock ticker recorded for later review.

## Trigger
A request arrives with a stock ticker symbol.

## Steps
1. Look up the current price of the ticker from the market data API.
2. Record the retrieved price in the audit log.

## Constraints
- Every lookup must be logged, even if the request is repeated for the same ticker.
