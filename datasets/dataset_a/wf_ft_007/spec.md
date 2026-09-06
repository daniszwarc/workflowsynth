# Workflow: Weekly Workout Plan Generation

## Context
The AI coach generates a personalized weekly workout plan based on the user's fitness goals, current level, and available equipment.

## Trigger
A user requests a new weekly workout plan.

## Steps
1. Authenticate the user.
2. Read the user's fitness profile, goals, and available equipment.
3. Read the user's recent workout history to understand current level.
4. Call the AI model to generate a personalized weekly plan.
5. Validate the generated plan is within the user's capability range.
6. Store the new training plan and set it as active.

## Constraints
- The new plan replaces the previous active plan.
- Plan must be validated for safety before being activated.
