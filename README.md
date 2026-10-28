# Bravura

Generate coherent synthetic business data with discoverable business situations, deterministic economics, and a separate answer key for evaluation.

## Current status

The first authoring milestone is implemented: research-role contracts and a bounded runner, evidence and dimension validation, offline replay, HTML review packets, and explicit version-bound design approval. The Apple v0.2 generator now produces and validates a 50,000-line synthetic release with a separate answer key. Live retrieval/model integration and blind analyst evaluation are not implemented. The supplied Signal package is a worked reference, not Bravura's architecture or required industry.

## Run the first milestone

Requires Python 3.11+, with no third-party runtime dependencies:

```bash
PYTHONPATH=src python -m bravura research examples/fictional-brief.json --replay examples/replay --out outputs/demo-001
PYTHONPATH=src python -m unittest discover -s tests -v
```

Open `outputs/demo-001/review.html`. This is a clearly fictional test fixture, not real company research or generated transactions. Use a fresh output directory for each run.

See [workflow documentation](docs/workflow.md) for contracts, the external-agent adapter, validation and approval commands.

## Generate the Apple slice

See [generation instructions and validation evidence](docs/generation.md). The release covers 30 months, 300 accounts and three interacting mechanisms, with explicit simulation and isolation limitations. Generated files remain outside Git.

## Agreed direction

Research the target organization first, then propose a recognizable business slice with declared dimensions and hierarchies, multiple purchasers per customer, and tens of thousands of transaction rows spanning at least two full years. Year-over-year comparisons are a core requirement. Review the dimension blueprint and stories together before generation.

## Design references

- [Research-led strategy and agent contracts](docs/research-led-strategy.md)
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
