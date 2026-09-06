# Workflow: Drupal Metadata Lookup

## Context
Before publishing an article to the CMS, the pipeline resolves three pieces of metadata: the author entity ID, the category taxonomy term UUID, and the magazine issue UUID via the CMS JSON:API.

## Trigger
An article has been categorised and is ready for publication.

## Steps
1. Look up the author entity in the CMS by author name using the JSON:API.
2. Look up the category taxonomy term UUID by category name.
3. Look up the magazine issue UUID by magazine issue number.
4. Merge the three lookup results into a single metadata record.

## Constraints
- All three lookups must succeed before article creation proceeds.
- If author not found, the article is flagged for manual assignment.
