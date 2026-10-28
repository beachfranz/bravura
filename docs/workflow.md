# Research-to-blueprint workflow v0.1

This release implements authoring contracts, five role assignments, a bounded role runner, an external-agent command interface, offline replay, review packet rendering and explicit design approval. It does not implement web retrieval, a model provider, transaction generation, row-level data validation or isolated analyst evaluation.

## Quick start (Python 3.11+)

No third-party runtime dependencies or API credentials are needed for the offline example. From the repository root:

```bash
export PYTHONPATH=src
python -m bravura plan examples/fictional-brief.json
python -m bravura research examples/fictional-brief.json --replay examples/replay --out outputs/demo-001
python -m bravura validate outputs/demo-001/bundle.json
python -m unittest discover -s tests -v
```

Open `outputs/demo-001/review.html` in a browser. Each run needs a new output directory. The fixture is a fictional company with an explicit unknown research claim and synthetic dimensions/stories. It is not Apple research, does not contain fake cited news, and has not generated 50,000 rows. That number is the proposed order-line target.

Optional installation: `python -m pip install -e .` exposes the same commands as `bravura`. Installation uses setuptools as a build dependency; running via PYTHONPATH avoids package downloads.

## Inputs and supported contracts

The complete executable example is `examples/fictional-bundle.json`. Contracts are version 1 and implemented in `src/bravura/contracts.py`; the original scenario template remains non-executable design guidance.

| Object | Required contents |
|---|---|
| Brief | schema_version=1, target, audience, purpose, questions[], constraints[], mode=recognizable_slice, start_date/end_date/reporting_cutoff, order_lines, budget |
| Budget | sources_per_role (1–30), timeout_seconds per command call (1–300) |
| Source | id, title, HTTP(S) url, published_date, accessed_date, snapshot_text containing text actually retrieved |
| Claim | id, statement, scope, status, period_start/end, evidence[]; reported claims need evidence, inferred claims need method and input_claim_ids, unknown claims need gap |
| Evidence | source_id, excerpt occurring in snapshot_text, location such as page/table/paragraph |
| Financial value | value, unit; monetary values use unit=money and three-letter currency. Preserve scale in the statement/method; this release does not normalize or reconcile financial values |
| Blueprint | slice, exclusions[], economic_policy, overlap_policy, dimensions[], relationships[], facts[], stories[] |
| Dimension | id, grain, primary_key, typed attributes, hierarchy[], unknown_policy, history_policy, generation_rule, provenance |
| Hierarchy level | id, key referencing an attribute, parent level ID or null; single-parent, acyclic declared levels |
| Provenance | kind=reported or synthetic, claim_ids[]; synthetic provenance needs rationale |
| Relationship | id, from/to dimension IDs, foreign_key, cardinality, temporal_rule, aggregation_rule; many_to_many also needs bridge |
| Fact | id, grain, primary_key, date_field, dimension_keys mapping dimension IDs to fact field names, measures[], allocation_policy |
| Story | id, title, status=simulated, mechanism, scope, comparison_basis, timing, effect_bounds, operational_evidence[], alternatives[], prohibited_claims[], claim_ids[]; without claims provide synthetic_rationale |
| Review | claim_reviews[] containing claim_id, disposition and reason; blockers[], warnings[], blueprint_assessment |

Identifiers use letters, digits, underscores and hyphens and begin with a letter. Dates are YYYY-MM-DD. Attribute types are string, integer, decimal, date and boolean. Unknown and conflicting claims cannot be accepted. Accepted inferences require accepted inputs. Blueprints cannot rely on unaccepted claims. Unknown claims may remain in a packet as acknowledged gaps.

The current validator checks declarations, not generated records. Temporal policies and effect bounds are text proposals; their execution and numerical checks belong to the generation milestone. It does not yet validate multiple purchasers per actual customer, temporal row assignments or financial identities because no rows exist.

## Agent execution

Roles run sequentially in v0.1: structure, financial, developments, lead, reviewer. Researchers receive the same brief and accumulated evidence. The lead receives consolidated research; the reviewer also receives the proposed blueprint. There are exactly five calls, no automatic retries, and no agent-controlled branching or approval. Future concurrency can preserve these contracts without adding a framework dependency.

For live research, provide a trusted executable that reads one task JSON from stdin and writes exactly one result JSON to stdout:

```bash
python -m bravura research my-brief.json --agent-command '["python", "my_research_adapter.py"]' --out outputs/live-001
```

The adapter must implement retrieval and model calls. It must read actual sources, retain relevant excerpts, obey source/token limits, and return the documented contracts. This release does not include a particular provider adapter. It has been tested with local subprocess fixtures; no live model-backed company research has been run.

Researcher results are `{ "sources": [...], "claims": [...] }`; IDs must start with `structure_`, `financial_`, or `developments_` respectively. Lead returns the blueprint object. Reviewer returns the review object. See `examples/replay/` for every role's response shape. The reviewer can reject evidence or retain uncertainty; it cannot approve the user's demo.

The command adapter launches an argument array without a shell, enforces wall-clock timeout, rejects nonzero exits/invalid JSON/responses over 2 MB, and withholds stderr from user-facing errors. The runner enforces source count and response contracts. This is a trusted local process interface, not a sandbox; the adapter runs with the current user's permissions. Provider tokens, retrieval query limits and independent source verification are the adapter's responsibility, not currently enforced by Bravura. Do not place credentials in brief files or command arguments.

## Outputs and approval

Successful runs write `bundle.json`, a self-contained escaped `review.html`, a `manifest.json` with bundle/source snapshot hashes, and `run.json` with backend mode and request/response hashes. Failed execution retains a failed trace and does not publish a successful bundle. Outputs are authoring-only and ignored by Git. Replaying identical inputs yields identical output contents.

After the user reviews the packet, an explicit command can record their approval:

```bash
python -m bravura approve outputs/demo-001/bundle.json --reviewer "Reviewer name" --note "Decision and acknowledged limitations" --out outputs/demo-001/approval.json
python -m bravura verify-approval outputs/demo-001/approval.json outputs/demo-001/bundle.json
```

These are instructions, not an approval of the included fixture. No approval is recorded automatically. Blockers or revise decisions prevent approval. The approval embeds the exact bundle and hash, refuses overwrite, and becomes invalid when the bundle changes. It is a local declaration, not authenticated signing or tamper-proof storage. Generation must eventually require a matching approved design plus its own stricter executable contracts.

## Verification and remaining work

The test suite exercises malformed evidence, post-cutoff sources, hierarchy cycles, purchaser/account cardinality, missing dimensions, unsupported claims, deterministic replay, adapter failure/timeout, HTML escaping and approval invalidation. Structural success is never presented as source authenticity, financial validation or blind-evaluation success.

Next: select a real target and audience; connect a retrieval/model adapter; validate its sourced organization brief with a human; complete executable scenario/economic contracts; implement and benchmark the 50,000-line generator; then enforce isolated analyst evaluation.
