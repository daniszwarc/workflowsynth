# Workflow: Water Intake Logging

## Context
Users log their daily water intake in millilitre increments. The app tracks progress toward the user's daily hydration target.

## Trigger
A user logs a water intake entry.

## Steps
1. Receive the water intake entry with amount in millilitres.
2. Validate the amount is within plausible range (1 -- 2000 ml per entry).
3. Store the entry and update the daily hydration total.

## Constraints
- Daily hydration target is set in the user's profile.
- Entries outside 1-2000 ml are rejected.
