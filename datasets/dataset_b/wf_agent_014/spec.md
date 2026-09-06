# Workflow: Full Agent Pipeline With Three Sources

## Context
A complete agent run: read its configuration, authenticate, gather data from three sources, classify it, route accordingly, transform, validate, store, and audit.

## Trigger
An agent run starts, driven by its own configuration.

## Steps
1. Read the agent's configuration.
2. Authenticate as the configured agent service.
3. Fetch data from the first source.
4. Fetch data from the second source.
5. Fetch data from the third source.
6. Classify the combined context from the three sources.
7. Route execution based on the classification.
8. Transform the routed data into the storage format.
9. Validate the transformed data before storing.
10. Store the validated result.
11. Log the full agent run for audit purposes.

## Constraints
- Authentication must occur before any of the three sources are fetched.
- The transformed data must be validated before storage.
