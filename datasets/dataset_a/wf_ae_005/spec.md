# Workflow: Post-Publication File Management

## Context
After an article is successfully published, the source PDF is moved to the completed folder in Google Drive and the Excel category spreadsheet is updated to mark the article as processed.

## Trigger
An article has been successfully published to the CMS.

## Steps
1. Move the source PDF from the pending folder to the completados folder in Google Drive.
2. Read the current state of the Excel category spreadsheet.
3. Update the article row in the spreadsheet to mark it as published.
4. Write an audit log entry confirming the file was moved and the registry updated.
