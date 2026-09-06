# Workflow: Input Form Validation and Storage

## Context
A public intake form must be validated against its expected schema before its data is persisted.

## Trigger
A form submission arrives from the public intake endpoint.

## Steps
1. Fetch the submitted form payload.
2. Validate the payload against the intake form schema.
3. Authenticate as the intake service before writing to storage.
4. Store the validated form data.

## Constraints
- Unvalidated form data must never be persisted.
