# Workflow: Body Weight Measurement Logging

## Context
Users log their body weight measurements. Historical weight data is used by the AI coach to track progress toward goals.

## Trigger
A user enters a body weight measurement.

## Steps
1. Receive the weight measurement with date and time.
2. Validate the measurement is within plausible range.
3. Store the measurement linked to the user.

## Constraints
- Measurements outside 30-300 kg are rejected as implausible.
- Only one measurement per day is recommended.
