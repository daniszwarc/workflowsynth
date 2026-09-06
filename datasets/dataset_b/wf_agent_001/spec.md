# Workflow: Config File Validation

## Context
A configuration file must be read and checked against its expected structure before anything relies on it.

## Trigger
A service startup process reads its configuration file.

## Steps
1. Read the configuration file contents.
2. Validate the configuration against its expected schema.

## Constraints
- The service must not proceed with a configuration that fails validation.
