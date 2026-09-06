# Workflow: Game and Schedule Management

## Context
Admins schedule games between two teams. Games drive the live scoring and standings workflows downstream.

## Trigger
An admin submits a game scheduling form.

## Steps
1. Receive the game scheduling form with home team, away team, league, date, time, and venue.
2. Authenticate the admin user.
3. Validate that both teams belong to the specified league.
4. Check for scheduling conflicts: no game for either team on the same date.
5. Apply the conflict rule.
6. Insert the game record with status 'scheduled'.

## Constraints
- Home and away teams must belong to the specified league.
- Game status: scheduled, live, finished.
- A team cannot play two games on the same date.
