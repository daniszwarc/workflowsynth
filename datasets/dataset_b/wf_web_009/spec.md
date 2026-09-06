# Workflow: Content Moderation Routing

## Context
A newly submitted post must be classified and routed to either the approval queue or the rejection queue.

## Trigger
A new post is submitted for moderation.

## Steps
1. Fetch the submitted post.
2. Classify the post using the moderation rule.
3. Route the post to the approve queue or the reject queue based on the classification.

## Constraints
- Every post must be routed to exactly one of the two queues -- never both, never neither.
