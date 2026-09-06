# Workflow: Streak and Achievement Tracking

## Context
The app tracks consecutive days of activity (streaks) and awards achievement badges. Streaks reset if a user misses a day.

## Trigger
A user logs any activity (nutrition or workout) for the day.

## Steps
1. Read the user's last activity date from the database.
2. Apply the streak continuation rule: if last activity was yesterday, increment streak.
3. Apply the streak reset rule: if last activity was more than 1 day ago, reset to 1.
4. Check if any achievement thresholds have been crossed.
5. Update the streak and award any new achievements.

## Constraints
- Streak increments only if the user logged activity on the previous calendar day.
- Achievements are awarded at streaks of 7, 30, and 100 days.
