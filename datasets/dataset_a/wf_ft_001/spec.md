# Workflow: User Registration and Profile Setup

## Context
A mobile fitness app onboards new users. Registration creates an auth account, then collects fitness profile data including goals, current stats, and dietary preferences to personalize the AI coach.

## Trigger
A new user completes the registration form on the mobile app.

## Steps
1. Receive the registration form with email, password, and basic profile data.
2. Create the authentication account via the Backend-as-a-Service.
3. Validate the profile data fields.
4. Create the user profile record linked to the auth account.
5. Log the registration event.

## Constraints
- Auth account creation must succeed before the profile record is created.
- Profile data includes fitness goals, current weight, height, and dietary preferences.
