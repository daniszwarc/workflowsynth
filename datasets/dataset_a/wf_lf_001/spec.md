# Workflow: PDF Text Extraction and Structure Detection

## Context
A French-language academic PDF reader extracts and structures text from an uploaded PDF entirely client-side. Headings are detected by comparing font sizes to the median body text size.

## Trigger
A user selects a PDF file in the browser.

## Steps
1. Receive the PDF file selected by the user.
2. Load the PDF and iterate over each page.
3. Extract all text items with their font size metadata.
4. Compute the median font size to establish the body text baseline.
5. Apply the heading detection rule: text items with font size significantly above the median are classified as headings.

## Constraints
- All extraction is client-side -- the PDF binary never leaves the browser.
- Heading detection uses font-size ratio comparison, not semantic analysis.
- Works only on PDFs with a text layer.
