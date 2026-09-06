# Workflow: Two-Source Data Merge

## Context
An analyst needs a single combined view built from two independent data sources that both describe the same entities.

## Trigger
A request arrives asking for the combined view of an entity across both sources.

## Steps
1. Fetch data from the first source.
2. Fetch data from the second source.
3. Merge both datasets into a single combined result.

## Constraints
- Both sources must be fetched fresh for every request -- no partial merges.
