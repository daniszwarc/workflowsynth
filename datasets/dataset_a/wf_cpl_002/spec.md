# Workflow: League Management

## Context
Admins create and manage leagues. Leagues are the top-level organizational unit that groups teams and games.

## Trigger
An admin submits a league create or update form.

## Steps
1. Receive the league form with name and display properties.
2. Authenticate the admin user.
3. Insert or update the league record.

## Constraints
- League name must be unique.
- Teams and games reference the league -- deleting a league with active records is prevented.
