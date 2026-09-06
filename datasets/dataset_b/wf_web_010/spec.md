# Workflow: User Registration

## Context
A new user registration must be validated, checked for duplicates, and a new account created, with a welcome email sent afterward.

## Trigger
A new user submits the registration form.

## Steps
1. Fetch the submitted registration payload.
2. Validate the registration payload against the registration schema.
3. Check whether the email address is already registered using the duplicate-check rule.
4. Authenticate as the registration service before creating the account.
5. Create the new account.
6. Send the welcome email to the new user.

## Constraints
- The duplicate check must run before the account is created.
- A welcome email must be sent for every successfully created account.
