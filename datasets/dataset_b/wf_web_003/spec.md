# Workflow: Structured Content Extraction

## Context
A page's content needs to be pulled and reduced to a small set of structured fields.

## Trigger
A request arrives to extract structured content from a given page.

## Steps
1. Scrape the page content.
2. Extract the structured fields from the scraped content.

## Constraints
- Only the requested structured fields should be returned -- not the raw page markup.
