# Workflow: AI Nutrition Coach Query

## Context
Users ask the AI nutrition coach questions. The coach retrieves the user's recent nutrition log and profile to provide personalized advice grounded in their actual data.

## Trigger
A user submits a question to the AI nutrition coach.

## Steps
1. Receive the user's question from the coach chat interface.
2. Authenticate the user.
3. Read the user's nutrition log for the last 7 days.
4. Read the user's fitness profile and goals.
5. Call the AI chat model with the user's question and nutrition context.
6. Return the AI response to the user.

## Constraints
- AI responses must be grounded in the user's actual nutrition data.
- The coach never provides medical advice.
