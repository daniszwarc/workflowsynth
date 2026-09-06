# Workflow: Daily Nutrition Log Entry

## Context
Users log their daily food intake. Each entry stores calories, macros, meal type, and timestamp. The AI food label scanner extracts nutritional data from photos automatically.

## Trigger
A user adds a food item to their nutrition log.

## Steps
1. Receive the food log entry with item name, meal type, and nutritional data.
2. Validate the entry fields.
3. Look up the food item in the nutrition database.
4. Compute daily totals for calories and macros.
5. Store the log entry linked to the user and date.

## Constraints
- Meal types: breakfast, lunch, dinner, snack.
- Daily totals are recomputed on every entry.
