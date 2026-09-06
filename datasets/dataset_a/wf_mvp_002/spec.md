# Workflow: Role-Based Menu Rendering

## Context
After login, the system renders a role-specific navigation menu. Admins see all sections, read-only users see view-only sections.

## Trigger
A user has successfully logged in.

## Steps
1. Read the authenticated user's role and admin flag from the session.
2. Fetch the user's role details from the database.
3. Apply the role routing rule to determine which menu sections to render.
4. Format and return the role-appropriate navigation menu.

## Constraints
- Three role tiers: admin (full access), readOnly (view only), manageAdmin (admin tools).
