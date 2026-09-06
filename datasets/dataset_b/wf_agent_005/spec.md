# Workflow: Intent Classification and Routing

## Context
An agent's incoming input must be validated, classified by intent, and routed to the appropriate handler.

## Trigger
A user input arrives for the agent to act on.

## Steps
1. Fetch the incoming user input.
2. Validate the incoming input against the expected input schema.
3. Classify the input's intent.
4. Route the input to the handler matching the classified intent.

## Constraints
- Routing must always be based on the freshly classified intent.
