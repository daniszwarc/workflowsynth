# Workflow: Live Game Scoring and Commentary Feed

## Context
During a live game, admins record match events in real time. When the game ends, standings are automatically recalculated for both teams.

## Trigger
An admin records a live match event.

## Steps
1. Receive the live event form with game ID, event type, team, player, and minute.
2. Authenticate the admin user.
3. Read the current game record and verify the game is in 'live' status.
4. Validate the event type is accepted (goal, yellow_card, red_card, var, substitution).
5. Insert the event record into the game_events table.
6. If event is a goal, update the game score.
7. Apply the game-end rule: if the event marks the game as finished, update status.
8. If game is finished, trigger the standings recalculation subworkflow for both teams.
9. Log the event.

## Constraints
- Events can only be recorded for games in 'live' status.
- Game end automatically triggers standings update for both teams.
- Standing updates are additive -- re-running on the same game risks double-counting.
