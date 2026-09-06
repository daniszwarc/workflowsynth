# Workflow: Claim Status and Management Reporting

## Context
The system generates multi-category claim status reports aggregating data across employer, activity, medical, litigation, lost-time, and incident categories for internal review and client reporting.

## Trigger
A user requests a claim status report.

## Steps
1. Receive the report request with date range, audience, and filter parameters.
2. Authenticate the requesting user.
3. Read employer summary data from the tenant database.
4. Read activity data (FCM, IME) from the tenant database.
5. Read medical, litigation, lost-time, and incident data.
6. Aggregate all categories into a unified report structure.
7. Format and return the report.

## Constraints
- All queries are scoped to the client tenant database.
- 60+ report variants exist -- per audience and date range.
- Report output is HTML formatted for print.
