# Workflow: PubMed Literature Search and Summarization

## Context
Once a case wiki has 3 or more pages, a literature search is automatically triggered. The system extracts clinical terms, searches PubMed, and summarizes findings into the wiki.

## Trigger
The case wiki has reached 3 or more pages with content.

## Steps
1. Check that the case wiki has 3 or more pages -- if not, skip.
2. Authenticate the pipeline service.
3. Extract key clinical terms from the anonymized wiki pages.
4. Search PubMed for relevant literature using the extracted terms.
5. Call the AI to summarize PubMed results in the context of the case.
6. Store the literature summary as an encrypted wiki page.

## Constraints
- Only triggered when wiki has 3 or more pages.
- PubMed search uses anonymized terms only -- no patient-identifying information.
- Literature summary is encrypted before storage.
