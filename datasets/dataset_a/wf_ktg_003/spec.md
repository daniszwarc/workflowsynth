# Workflow: Medical Provider Registration

## Context
Administrators register medical providers in the network directory used for claimant referrals.

## Trigger
An admin submits a provider registration form.

## Steps
1. Receive the provider registration form.
2. Authenticate the admin user.
3. Validate the required provider fields.
4. Insert the provider record.
5. Insert the provider speciality record.

## Constraints
- Provider ID is generated via MAX(provider_id)+1 -- non-atomic under concurrency.
- Each provider can have multiple speciality records.
