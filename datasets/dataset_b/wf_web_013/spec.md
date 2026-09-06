# Workflow: Forum Thread Escalation

## Context
A reported forum thread must be classified, and severe cases escalated to a senior moderator rather than handled by the standard queue.

## Trigger
A forum thread is reported by a user.

## Steps
1. Fetch the reported thread's content and report metadata.
2. Validate the report data against the report schema.
3. Classify the severity of the report using the escalation rule.
4. Route the thread to the standard moderation queue or the senior escalation queue based on severity.
5. Notify the senior moderator when a thread is escalated.
6. Log the moderation decision for audit purposes.

## Constraints
- A thread must only reach the senior escalation queue when the escalation rule flags it as severe.
