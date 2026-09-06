# Workflow: Adversarial Analysis Loop Iteration

## Context
Two frontier LLMs run against each other in an adversarial loop. Each iteration produces new findings compared against the previous to determine convergence.

## Trigger
An analysis iteration is triggered.

## Steps
1. Receive the case context and previous iteration findings.
2. Authenticate the analysis service.
3. Call the first LLM with the case context and previous findings.
4. Encrypt the first LLM response before storing.
5. Call the second LLM with the case context and the first LLM's challenges.
6. Encrypt the second LLM response before storing.
7. Apply the convergence check: < 10% new items = converged.
8. Store both responses and log the iteration.

## Constraints
- MAX_ITERATIONS = 8. The loop never runs more than 8 iterations.
- CONVERGENCE_THRESHOLD = 0.10.
- All LLM prompts and responses are encrypted at rest.
- Cancellation is supported via case_id keyed cancellation dict.
