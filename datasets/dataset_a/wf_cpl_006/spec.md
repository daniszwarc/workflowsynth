# Workflow: Manual Game Result Entry

## Context
Admins manually enter or correct game results for games not tracked live. The final score is entered and standings are recalculated.

## Trigger
An admin manually enters a game result.

## Steps
1. Receive the result entry form with game ID, home score, and away score.
2. Authenticate the admin user.
3. Validate the scores are non-negative integers.
4. Update the game record with final scores and status 'finished'.
5. Trigger the standings recalculation subworkflow.

## Constraints
- Only applicable to games in 'scheduled' or 'live' status.
- Editing a result that already updated standings risks double-counting.
