# Workflow: Wiki Page Rebuild Trigger

## Context
Authorized administrators can trigger a rebuild of one or all wiki pages in the clinical knowledge base.

## Trigger
An administrator triggers a wiki rebuild for a specific page.

## Steps
1. Receive the wiki rebuild request specifying the page name.
2. Authenticate the requesting user -- only admin role can trigger rebuilds.
3. Validate the page name is one of the 10 known wiki pages.
4. Trigger the wiki compiler subworkflow for the specified page.

## Constraints
- Only admin role can trigger wiki rebuilds.
- Valid pages: timeline, diagnoses, treatments, labs_trends, labs_microbiology, imaging, medications, trials, hospitalizations, other.
