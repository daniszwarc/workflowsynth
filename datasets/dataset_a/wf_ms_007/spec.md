# Workflow: NCT Clinical Trial Validation

## Context
Clinical trial NCT numbers in analysis findings are validated against the ClinicalTrials.gov API to confirm they exist.

## Trigger
Analysis findings have been generated and contain NCT numbers.

## Steps
1. Extract all NCT numbers from the analysis findings.
2. Authenticate the validation service.
3. For each NCT number, query the ClinicalTrials.gov API v2.
4. Apply the validation rule: mark each NCT as valid or invalid.
5. Store the validation results linked to the analysis findings.

## Constraints
- All NCT numbers must be validated before the report is generated.
- Invalid NCT numbers are flagged, not silently removed.
- Uses ClinicalTrials.gov API v2.
