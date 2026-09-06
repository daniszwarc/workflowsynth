# Workflow: Season and Finals Management

## Context
Admins create and manage seasons and playoff finals. Seasons are the top-level grouping for leagues and games.

## Trigger
An admin submits a season or finals form.

## Steps
1. Receive the season or finals form.
2. Authenticate the admin user.
3. Validate the season data.
4. Insert the season or finals record.

## Constraints
- Only one season can be active at a time.
- Finals are linked to a specific season and league.
