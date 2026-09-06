# Workflow: Daily Progress Statistics

## Context
The stats screen displays the user's progress toward their daily nutrition targets and weekly workout goals.

## Trigger
A user opens the stats screen.

## Steps
1. Authenticate the user.
2. Read today's nutrition log entries for the user.
3. Aggregate calories and macros consumed today.
4. Compare against the user's daily targets and format the progress summary.

## Constraints
- Stats are computed fresh on every screen load.
- Daily targets come from the user's profile.
