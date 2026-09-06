# Workflow: Forum Comment Posting With Moderator Alert

## Context
A user posts a comment to a forum thread, and the moderation team should be alerted so they can review it.

## Trigger
A user submits a new comment on a forum thread.

## Steps
1. Fetch the submitted comment payload.
2. Validate the comment payload against the comment schema.
3. Authenticate the posting user before the comment is published.
4. Publish the comment to the forum thread.
5. Extract the publish status from the platform's response.
6. Notify the moderation team that a new comment needs review.

## Constraints
- A comment must never be published without the posting user being authenticated first.
