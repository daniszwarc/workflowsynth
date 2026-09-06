# Workflow: Convergence Check and Wiki Update

## Context
After each adversarial analysis iteration, the system checks convergence. When converged or max iterations reached, finalized findings are written to the wiki.

## Trigger
An analysis iteration has completed.

## Steps
1. Read the current and previous iteration findings.
2. Apply the convergence rule: < 10% new items or MAX_ITERATIONS reached.
3. If not converged, route back to analysis loop.
4. If converged, encrypt the final findings.
5. Write the converged findings to the case wiki as a full page replacement.

## Constraints
- Convergence: < 10% new items in current iteration vs total.
- Wiki update uses full page replacement -- never a diff.
- Final findings must be encrypted before wiki storage.
