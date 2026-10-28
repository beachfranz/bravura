# Initial implementation plan

## Baseline assessment

The GitHub repository was empty when inspected. No pre-existing Bravura implementation or project instructions were available. Business mechanisms, multi-table coherence, deterministic economics, baseline variation, scenario overlap, answer keys, reproducibility, and fresh-context evaluation are all proposed capabilities, not verified Bravura behavior.

The Signal reference includes generators and operational CSVs. Reading its existing files and recalculating totals does not establish regeneration, analyst isolation, or fresh-context evaluation. Its packaged scenario run records seed 78123, while the README example uses 73191. It has ten operational tables and no inventory snapshots. The standalone audit is historical.

## Smallest end-to-end slice

Start with a local Python command-line generator using standard-library CSV, JSON, decimal arithmetic, hashing, seeded randomness, and unittest. This is a new implementation choice, not a migration. No paid service, LLM API, database, or agent framework is required for generation.

1. Define configurable accounts, contacts, products, cost versions, calendar, prices, and ordinary demand variation. Keep names and business labels configurable.
2. Generate orders, fulfillments, routine returns, and neutral account activity with stable keys and a single reporting cutoff.
3. Implement a margin-deterioration mechanism and derive all dependent economics.
4. Add partial-explanation account decline and weak-contribution promotion mechanisms, including benign comparison cohorts and shared populations.
5. Produce baseline, isolated scenario states, and the final combined state. Persist affected records and component effects in the answer key.
6. Export only operational allowlisted files. Retain authoring inputs and answer keys separately.
7. Verify repeatability and combined-state release gates before attempting isolated analyst evaluation.

## Scenario primitives

| Primitive | Parameters and dependencies | Operational evidence | Required uncertainty |
|---|---|---|---|
| Growth with margin deterioration | Effective-dated supplier cost, price response, demand mix, expedite share | Cost history, orders, products, shipments | Multiple mechanisms; discounts need not dominate |
| Concentrated account decline | Affected accounts, purchasing reduction, lagged service disruption for a subset | Account rollups, plans, order cadence, delivery dates, routine activity | At least one material decline has no supported cause; no fabricated churn or competitor loss |
| Promotional growth with weak contribution | Eligibility, dates, price reduction, demand response, program cost, returns, fulfillment | Promotion terms, order cohorts, returns, shipments | Same-product benchmarks are descriptive; only the evaluator sees simulated causal contrasts |

Freeze effect bounds before generating release data. Failed bounds require a generator/configuration repair or rejected run, not rewritten expected answers. Include profitable promotions, intentional concessions, unaffected accounts, and ordinary operational failures.

## Economics and composition

Define rounding and allocation policies before implementation. Use decimal values, allocate order-level costs once, reconcile allocations, and explicitly handle zero denominators. Track pre-return gross profit separately from return-adjusted contribution. Do not subtract refunds or inventory recovery twice.

Use stable random streams per entity and mechanism so intervention comparisons do not change unrelated noise. Compose events in declared temporal/dependency order. For each metric and scope, report combined-minus-baseline effect, isolated effects, and interaction residual = combined effect minus sum of isolated effects. Do not present isolated effects as additive when interactions exist.

## Pass/fail release gates

| Gate | Pass condition |
|---|---|
| Structure | Unique primary keys; all required foreign keys resolve; declared cardinalities hold |
| Time | Valid event sequence; exactly one applicable cost version per transaction; no post-cutoff evidence |
| Finance | Exact equality under declared decimal rounding policy; allocations reconcile to source totals; no unknown cost treated as zero |
| Returns | Cumulative returned units do not exceed sold units; credits and recovery reconcile |
| Plausibility | Configured baseline distributions and ordinary exception rates meet predeclared bounds |
| Combined scenarios | All intended effects survive in the final state within frozen bounds; overlap and residual reconcile |
| Reproducibility | Same pinned code, dependencies, configuration, and seed reproduce content hashes; volatile metadata excluded explicitly |
| Export | Exact allowlist; no answer-bearing fields, names, notes, metadata, or files |
| Isolation | Analyst environment cannot read repository, parent authoring paths, answer keys, or counterfactuals; negative access tests pass |
| Analyst evaluation | Fresh context returns frozen evidence-backed findings; quantification uses matching comparison bases; unsupported causal/intent claims fail; unexplained decline remains unexplained |

Set detection, prioritization, numerical-error, evidence, and abstention thresholds and evaluation sample sizes before the first blind run. Test varied seeds and entity names. A good-looking briefing is not a release gate by itself.

## Build and reuse

Build scenario contracts, mechanism composition, economic policies, answer-key calculation, export policy, and domain validation as Bravura-owned logic. Reuse standard-library serialization, decimal arithmetic, hashing, and testing initially. Consider table/analytics libraries only when demonstrated data volume or ergonomics justify them. No vendor or orchestration dependency is selected by the Signal reference.

## Delivery evidence

Each release must retain configuration, code/dependency versions, input/output hashes, deterministic validation results, final combined-state summaries, and evaluator-only truth. Analyst execution and scoring are separate stages. Until isolation and analyst execution exist, mark them not run rather than passing them implicitly.
