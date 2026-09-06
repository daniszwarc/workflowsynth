# Workflow: Two-Tier Clinical Report Generation

## Context
Analysis findings are structured into a two-tier report: documented (from patient records with citations) and inferred (model reasoning). The two tiers must remain separated.

## Trigger
Converged analysis findings are ready for report generation.

## Steps
1. Read the converged analysis findings.
2. Authenticate the report generation service.
3. Classify findings by tier: documented (with citation) vs inferred (reasoning only).
4. Apply the promotion rule: inferred can upgrade to documented only with a source citation.
5. Validate that no finding has a self-assessed confidence label.
6. Encrypt the report content before storage.
7. Store the two-tier report.
8. Log report generation.

## Constraints
- Two tiers must remain separated: documented vs inferred.
- Inferred to documented promotion requires an explicit source citation.
- No self-assessed confidence labels: no 'high confidence', 'critical urgency'.
- This is NOT a certified medical device.
