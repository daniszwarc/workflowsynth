# Workflow: Filtered Search with Notification

## Context
A user wants search results narrowed down to only relevant matches, with an alert sent when relevant matches are found.

## Trigger
A search query arrives from a monitoring subscription.

## Steps
1. Search for matches to the subscribed query.
2. Filter the results down to only the relevant matches.
3. Notify the subscriber that relevant matches were found.

## Constraints
- The subscriber should only be notified when at least one relevant match exists.
