# Workflow: Exercise Database Lookup

## Context
Users search the exercise database when building workout sessions. Each exercise has instructions, muscle groups, and equipment requirements.

## Trigger
A user searches for an exercise by name or muscle group.

## Steps
1. Receive the search query with name or muscle group filter.
2. Read matching exercises from the exercise database.
3. Return the matching exercises with details.

## Constraints
- Search is case-insensitive and supports partial name matching.
