# Workflow: Clinical Alert Generation

## Context
The dashboard automatically generates clinical alerts based on deterministic threshold rules applied to the patient's lab values. No LLM involvement -- fixed clinical thresholds only.

## Trigger
The dashboard loads or a scheduled check runs.

## Steps
1. Read the most recent lab values from the clinical database.
2. Authenticate the requesting user.
3. Apply the neutrophil threshold rule: < 1.5 = warning, < 0.5 = critical.
4. Apply the hepatic panel rules: GOT and GPT thresholds.
5. Apply the CA 15-3 rise rule and RB1 detection rule.
6. Merge and format all alerts with severity levels.

## Constraints
- Alerts use deterministic threshold rules -- no LLM involved.
- Every alert links to the source document.
