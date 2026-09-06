# Dataset A -- Enterprise Workflow Synthesis Tasks

133 real enterprise workflow synthesis tasks drawn from 20+ years of
professional experience across insurance, healthcare, manufacturing,
publishing, sports media, and enterprise knowledge management.

## Structure

Each task directory contains:
- `spec.md` -- Natural language specification (LLM input only)
- `reference_dsl.yaml` -- Reference DSL implementation (ground truth, never shown to LLM)
- `tests/test_{wf_id}.py` -- Pytest suite verifying candidate correctness

## Domain Breakdown

| Domain | Prefix | Count |
|---|---|---|
| Insurance Brokerage | wf_pb | 15 |
| Health and Fitness | wf_ft | 13 |
| Publishing | wf_ae | 6 |
| Community Sports | wf_sv | 6 |
| Clinical AI | wf_mm | 8 |
| Clinical AI | wf_btp | 9 |
| Healthcare Billing | wf_erd | 12 |
| Clinical AI Research | wf_ms | 9 |
| Manufacturing | wf_mvp | 11 |
| Enterprise Knowledge | wf_aw | 10 |
| Community Sports Admin | wf_ts | 9 |
| Sports Media | wf_cpl | 10 |
| Personal Tool | wf_lf | 4 |
| Workers Compensation | wf_ktg | 11 |
| **Total** | | **133** |

## Anonymization

All client names, personal names, and identifying URLs have been replaced
with generic descriptors. All workflows are sourced from real professional
projects -- no invented workflows.
