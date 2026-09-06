# Workflow: Standings Recalculation

## Context
When a game finishes, standings are updated for both teams. Points, wins, draws, losses, goals for, and goals against are recalculated.

## Trigger
A game has finished (triggered by live scoring or manual result entry).

## Steps
1. Receive the finished game record with final score and team IDs.
2. Authenticate the triggering service.
3. Read the current standings rows for both teams.
4. Apply the result classification rule: win/draw/loss for each team.
5. Update the standings accumulators for both teams.
6. Log the standings update.

## Constraints
- Standings are additive accumulators -- not recomputed from scratch.
- Win = 3 points, Draw = 1 point each, Loss = 0 points.
- Called by both live scoring and manual results.
