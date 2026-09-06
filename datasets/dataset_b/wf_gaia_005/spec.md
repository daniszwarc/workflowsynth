# Workflow: News Feed Headline Extraction

## Context
A user wants just the headlines from a news feed, without the full article bodies.

## Trigger
A request arrives for the latest headlines from a configured news feed.

## Steps
1. Fetch the latest items from the news feed.
2. Extract just the headline field from each item.

## Constraints
- Only the headline field should be returned -- article bodies must be dropped.
