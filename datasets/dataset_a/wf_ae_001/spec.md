# Workflow: PDF Article Extraction via AI Vision

## Context
An economics magazine automates the extraction of article content from PDF files stored in Google Drive. Each PDF is sent to an AI vision model that extracts structured content including title, author, section, lead, body text, highlighted quotes, and sidebars.

## Trigger
A PDF file is found in the pending articles folder in Google Drive.

## Steps
1. Search Google Drive for PDF files in the pending articles folder.
2. Download the PDF file binary from Google Drive.
3. Send the PDF binary to the AI vision API with a structured extraction prompt.
4. Parse the AI response JSON, stripping any markdown fences.
5. Validate that required fields are present (title, section, content).

## Constraints
- The AI must handle two formats: single article and multiple book reviews (es_multiple = true).
- Double quotes inside content must be replaced with single quotes to preserve JSON validity.
- The lead field must never be empty.
