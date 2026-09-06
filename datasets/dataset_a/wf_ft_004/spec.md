# Workflow: Workout Session Logging

## Context
Users log their gym workout sessions. Each session records the exercises performed, sets, reps, and weights. Sessions are linked to the user's training plan.

## Trigger
A user completes a workout session.

## Steps
1. Receive the workout session data with exercise list, sets, reps, and weights.
2. Validate the session data.
3. Look up the user's current training plan.
4. Store the workout session linked to the user and date.
5. Update the training plan progress.

## Constraints
- Sessions must be linked to the user's active training plan.
- Volume (sets x reps x weight) is computed and stored per exercise.
