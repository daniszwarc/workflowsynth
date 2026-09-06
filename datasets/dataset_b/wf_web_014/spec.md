# Workflow: Multi-Step Content Publishing With Approval

## Context
A drafted piece of content must pass an editorial approval rule and, if approved, be handed off to the publishing subsystem, with the outcome logged either way.

## Trigger
An editor submits a draft for the publishing approval workflow.

## Steps
1. Fetch the content draft.
2. Validate the draft against the editorial schema.
3. Apply the editorial approval rule to the validated draft.
4. Route the draft to the publishing subworkflow if approved, or the revision queue if not.
5. Delegate publishing to the publishing subworkflow when approved.
6. Log the final publishing decision.

## Constraints
- Content must never be handed to the publishing subworkflow without first passing the approval rule.
