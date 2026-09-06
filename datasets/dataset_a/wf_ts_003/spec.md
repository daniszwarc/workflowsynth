# Workflow: Payroll Report Generation and Export

## Context
The admin generates payroll reports for a date range filtered by role and pay_status. The report computes total pay per staff member and exports as Excel or PDF for external payment processing.

## Trigger
An admin requests a payroll report.

## Steps
1. Receive the report request with date range, role filter, and pay_status filter.
2. Authenticate the admin user.
3. Read timesheet records for the specified date range.
4. Filter by role and pay_status (authorized or processed).
5. Aggregate totals by staff member.
6. Apply the export format rule: route to Excel or PDF export.
7. Generate the export file.
8. Log the report generation.

## Constraints
- Only admin role can generate payroll reports.
- pay_status values: AUT (authorized for payment), SPD (already processed).
- This is a reporting tool only -- no actual payment execution occurs in the system.
