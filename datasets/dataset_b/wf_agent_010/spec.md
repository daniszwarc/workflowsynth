# Workflow: Config-Driven Conditional Execution

## Context
A workflow's behaviour must be driven by its configuration: read it, apply the rules it defines, and execute the branch it selects.

## Trigger
A configurable job starts and needs to read its own configuration to decide what to do.

## Steps
1. Read the job configuration.
2. Apply the rule defined by the configuration to the current input.
3. Route execution to the branch selected by the rule's outcome.

## Constraints
- The configuration must be read fresh at the start of every run.
