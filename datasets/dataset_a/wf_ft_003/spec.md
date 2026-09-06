# Workflow: Food Label AI Scanning

## Context
Users photograph food product labels with their phone camera. The AI vision model extracts nutritional information and pre-populates the food log entry form.

## Trigger
A user takes a photo of a food product label.

## Steps
1. Receive the image from the phone camera.
2. Validate the image format and size.
3. Send the image to the AI vision model API to extract nutritional data.
4. Parse the AI response and extract calories, macros, and serving size.
5. Validate the extracted nutritional data is within plausible ranges.
6. Return the pre-populated food entry form to the user for confirmation.

## Constraints
- The AI extraction must be confirmed by the user before the log entry is created.
- Implausible values (e.g. > 2000 calories per serving) are flagged for review.
