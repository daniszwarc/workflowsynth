# Workflow: Full Article Publishing Pipeline

## Context
The complete end-to-end publishing pipeline for the economics magazine. Processes each PDF article from Google Drive through AI extraction, category matching, CMS metadata lookup, publication, and file management. Reduced per-article processing time from 30 minutes to under 3 minutes.

## Trigger
A PDF article is found in the pending articles folder in Google Drive.

## Steps
1. Search Google Drive for PDF files in the pending articles folder.
2. Download each PDF binary.
3. Send the PDF to the AI vision API to extract structured article content.
4. Parse and validate the AI extraction response.
5. Handle the multi-article case: if es_multiple = true, loop over each review.
6. For each article, normalise the title and match against the Excel category spreadsheet.
7. Convert plain text content to HTML, handling interview format.
8. Look up author ID, category UUID, and magazine UUID in the CMS.
9. Retrieve a CSRF token for authenticated CMS write operations.
10. Authenticate the publishing user.
11. Create paragraph block entities in the CMS for each content section.
12. Create the article node in the CMS with all metadata and paragraph references.
13. Move the source PDF to the completados folder and update the Excel registry.

## Constraints
- CSRF token must be obtained before any CMS write operation.
- Paragraph blocks must be created before the article node.
- Articles with no Excel match are flagged for review but still published with default category.
- Full audit trail required for every published article.
