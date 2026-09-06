# Workflow: Three-Source Aggregation With Error Handling

## Context
A consolidated view must be built from three independent sources, tolerating the failure of any single source.

## Trigger
A request arrives asking for a consolidated view across three sources.

## Steps
1. Fetch data from the first source.
2. Fetch data from the second source.
3. Fetch data from the third source.
4. Aggregate the three datasets into a single view.
5. Handle any error that occurred while aggregating, rather than failing the whole request.

## Constraints
- A failure in any single source must not prevent a partial consolidated view from being returned.
