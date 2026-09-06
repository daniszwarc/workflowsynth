# Workflow: Article Publishing

## Context
A drafted article needs to be published to the content management system.

## Trigger
An editor triggers publication of a completed article draft.

## Steps
1. Fetch the article draft from the content management API.
2. Validate the draft against the article schema.
3. Authenticate as the publishing service before publishing.
4. Publish the article to the content management system.

## Constraints
- An article must never be published without an authenticated publishing action.
