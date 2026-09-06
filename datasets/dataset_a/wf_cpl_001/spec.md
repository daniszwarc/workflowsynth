# Workflow: Team Registration and Standings Row Initialization

## Context
An admin registers a new team in the sports news system. Team creation automatically initializes a standings row for the team in the current season.

## Trigger
An admin submits a new team registration form.

## Steps
1. Receive the team registration form with name, logo, league, and season.
2. Authenticate the admin user.
3. Validate the team data.
4. Insert the team record into the teams table.
5. Apply the standings initialization rule: create a standings row with all counters at zero.
6. Log the team creation.

## Constraints
- Every new team must have a standings row created at registration time.
- Team is associated with a league and season at creation.
- Hiding a team (soft delete) removes it from public display but preserves the record.
