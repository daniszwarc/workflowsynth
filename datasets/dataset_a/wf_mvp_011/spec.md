# Workflow: Repair Report Excel Export

## Context
Management generates Excel reports combining repair data with ERP item and vendor data for a specified date range.

## Trigger
An admin or office user requests a repair report.

## Steps
1. Receive the report request with date range and filter parameters.
2. Authenticate the admin or office user.
3. Read repair records from the local database joined with ERP item data.
4. Filter records by the requested criteria.
5. Format the filtered records as a structured Excel spreadsheet.

## Constraints
- Reports join local service DB with ERP.
- Date range filter is always required.
- Output format: Excel file for download.
