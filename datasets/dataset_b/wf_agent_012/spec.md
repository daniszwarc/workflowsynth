# Workflow: Multi-Agent Delegation and Synthesis

## Context
A complex task must be classified, delegated to a specialised subworkflow, and the subworkflow's result synthesised into a final answer.

## Trigger
A complex task arrives that a single agent step cannot fully resolve.

## Steps
1. Classify the task to determine which specialised subworkflow should handle it.
2. Delegate the task to the selected subworkflow.
3. Merge the subworkflow's result together with the original task context.
4. Format the merged result into the final synthesised answer.

## Constraints
- The final answer must incorporate the subworkflow's result, not just the original task.
