# Workflow: Verified Knowledge Graph Update

## Context
New data must be fetched, validated, merged into the existing knowledge graph, checked for consistency, stored, and stakeholders notified.

## Trigger
A knowledge update job runs with new candidate data for the graph.

## Steps
1. Fetch the new candidate data for the knowledge graph.
2. Validate the candidate data against the knowledge graph schema.
3. Merge the validated data into the existing graph data.
4. Verify the merged graph for consistency using the consistency rule.
5. Authenticate as the graph update service before storing.
6. Store the verified, merged graph update.
7. Notify stakeholders that the knowledge graph was updated.

## Constraints
- The merged update must pass the consistency check before it is stored.
