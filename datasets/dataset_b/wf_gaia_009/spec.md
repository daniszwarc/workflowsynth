# Workflow: API Data Transformation and Storage

## Context
Data pulled from an external API must be reshaped into the internal format before being saved.

## Trigger
A scheduled sync job triggers a pull from the external API.

## Steps
1. Fetch the latest data from the external API.
2. Transform the data into the internal record format.
3. Authenticate as the sync service before writing.
4. Store the transformed data.

## Constraints
- Data must be transformed into the internal format before it is ever persisted.
