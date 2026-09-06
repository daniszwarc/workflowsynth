# Workflow: Agent Task Routing to Subworkflow

## Context
An incoming agent task must be classified, a business rule applied, and the task routed to the correct subworkflow.

## Trigger
A new task is queued for the agent.

## Steps
1. Classify the incoming task.
2. Apply the routing rule to the classified task.
3. Route the task to the subworkflow matching the rule's outcome.

## Constraints
- A task must never be routed to a subworkflow before both classification and the routing rule have run.
