# Workflow: Lab Trend Time Series Load

## Context
The dashboard displays sparkline charts for key lab parameters over time. For each parameter, the time series of all historical values is loaded from raw documents.

## Trigger
A user loads the dashboard trends view for a specific parameter.

## Steps
1. Receive the request specifying the lab parameter to trend.
2. Authenticate the requesting user.
3. Read all lab result documents from the raw store, filtering for the requested parameter.
4. Format the results as an ordered time series with date and value pairs.

## Constraints
- Only Spanish source files are used -- .en.md translation files are excluded.
- Results are ordered chronologically.
