# Workflow: Multi-Step Research Pipeline

## Context
A research task requires gathering data, validating it, reshaping it, saving it, and alerting the requester once complete.

## Trigger
A research request arrives specifying a topic to investigate.

## Steps
1. Fetch source data relevant to the research topic.
2. Validate the source data against the expected research schema.
3. Transform the validated data into the research report format.
4. Authenticate as the research service before saving the report.
5. Store the finished research report.
6. Notify the requester that the report is ready.

## Constraints
- The requester must only be notified after the report has been successfully stored.
