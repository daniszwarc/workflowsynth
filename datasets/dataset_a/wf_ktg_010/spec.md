# Workflow: Bulk Triage and FROI Distribution

## Context
A batch workflow re-processes triage claims and distributes First Report of Injury (FROI) incident reports to insurers, adjusters, and employers.

## Trigger
Scheduled task or manual admin run.

## Steps
1. Trigger the batch run.
2. Authenticate the triggering service or admin.
3. Read all triage claims flagged for reprocessing.
4. Apply the FROI distribution rule to determine which parties receive the report.
5. Send the FROI incident report to each required recipient.

## Constraints
- FROI distribution is regulatory -- must reach all required parties.
- Trigger mechanism: may be scheduled task or manual admin run.
