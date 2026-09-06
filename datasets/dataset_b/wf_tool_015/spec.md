# Workflow: Full Four-Source API Integration

## Context
A complete integration pipeline: authenticate, gather data from four sources, merge, validate, encrypt, persist, notify, and audit the whole run.

## Trigger
A scheduled full-integration run triggers across four data sources.

## Steps
1. Authenticate as the integration service.
2. Fetch data from the first source.
3. Fetch data from the second source.
4. Fetch data from the third source.
5. Fetch data from the fourth source.
6. Merge all four datasets into a single combined result.
7. Validate the merged result against the integration schema.
8. Extract the sensitive fields from the validated result.
9. Encrypt the extracted sensitive fields.
10. Store the encrypted result.
11. Notify the integration owner that the run completed.
12. Log the full integration run for audit purposes.

## Constraints
- Authentication must occur before any of the four sources are fetched.
- The merged result must be validated and encrypted, in that order, before it is stored.
