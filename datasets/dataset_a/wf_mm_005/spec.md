# Workflow: Clinical Data Verification

## Context
After structuring, each document is verified to confirm no clinical values were lost or altered during AI processing. Every number with 2 or more digits and every date must appear unchanged in the Markdown output.

## Trigger
A document has been structured and is ready for verification.

## Steps
1. Extract all numbers (2+ digits) and dates from the original source text.
2. Extract all numbers and dates from the structured Markdown output.
3. Compare the two sets: identify any values missing from or altered in the Markdown.
4. Apply the confidence rule: 0 issues = high, 1-2 = medium, 3+ = low (flag for review).
5. Write the confidence level and any issues to the document metadata.

## Constraints
- All numbers with 2+ digits from the source must appear unchanged in the output.
- All dates from the source must appear unchanged in the output.
- Documents with confidence = low go to review queue, not to raw/.
