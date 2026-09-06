# Workflow: Authenticated Profile Update

## Context
A logged-in user wants to update their profile information.

## Trigger
A profile update request arrives from an authenticated session.

## Steps
1. Authenticate the requesting user.
2. Fetch the user's current profile data.
3. Validate the requested profile changes against the profile schema.
4. Update the profile record with the requested changes.

## Constraints
- The profile must never be updated without the user being authenticated first.
