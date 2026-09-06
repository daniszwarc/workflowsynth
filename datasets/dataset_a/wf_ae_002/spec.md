# Workflow: Article Category Matching from Excel

## Context
After extracting article content from a PDF, the pipeline matches each article title against a category spreadsheet maintained by the editorial team using fuzzy matching that handles accents and punctuation differences.

## Trigger
An article has been extracted and needs category assignment.

## Steps
1. Read the category mapping spreadsheet from Google Drive.
2. Extract the article title from the extracted article data.
3. Normalise both the article title and all spreadsheet titles: remove accents, lowercase, strip non-alphanumeric characters.
4. Apply the category matching rule to find the spreadsheet row whose normalised title matches.
5. If no match found, apply default category values and flag the article as needing editorial review.

## Constraints
- Matching must be accent-insensitive and punctuation-insensitive.
- Unmatched articles must be flagged with needs_review = true, not rejected.
- Default category: 'Ciencia economica'. Default section: 'Dossier'.
