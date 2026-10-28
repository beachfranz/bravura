# Bravura

Generate coherent synthetic business data with discoverable business situations, deterministic economics, and a separate answer key for evaluation.

## Current status

Repository foundation only. No Bravura generator or analyst evaluation has been implemented yet. The supplied Signal package is a worked reference, not Bravura's architecture, required industry, or verified implementation.

## Design references

- [Narrative generation playbook](docs/reference/Bravura_Narrative_Generation_Playbook.md)
- [Scenario contract design template](docs/reference/Scenario_Contract_Template.json)
- [Implementation plan and release gates](docs/implementation-plan.md)

## Intended layout

- `src/bravura/`: generator and deterministic validation logic.
- `tests/`: financial fixtures, scenario composition, and release checks.
- `docs/reference/`: versioned authoring requirements.
- `outputs/`: locally generated business data and answer keys; excluded from Git.

The JSON template is design guidance, not an executable or supported schema.

## Data boundaries

Authoring can use the source code, reference materials, scenario definitions, and answer key. Blind analysts receive only an allowlisted operational export, neutral data dictionary, metric policy, and reporting cutoff in a separate environment. Repository access would expose the answers and invalidate a blind test.

Generated datasets, credentials, and local environment files must not be committed. Record seeds, configurations, dependency versions, and content checksums so released datasets can be reproduced.
