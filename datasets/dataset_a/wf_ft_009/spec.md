# Workflow: Nutrition Target Update

## Context
When a user updates their fitness goals or body stats, the AI recalculates their daily nutrition targets (calories, protein, carbs, fat).

## Trigger
A user updates their fitness profile or goals.

## Steps
1. Receive the updated profile data.
2. Validate the updated fields.
3. Call the AI model to recalculate optimal daily nutrition targets.
4. Update the user profile with new targets.

## Constraints
- Nutrition targets are always derived from the user's current profile -- never hardcoded.
- Targets are recalculated on every significant profile change.
