# Repeatable story recipes — v0.4

Recipes are authoring assets, never analyst instructions. `PYTHONPATH=src python -m bravura recipes` exports five versioned recipes: margin deterioration, partially explained account decline, weak promotional contribution, customer lifecycle/concentration, and quality returns with lagged purchasing response. The historical contract JSON remains design guidance, not a supported input schema.

## Repeatable process for another dataset

1. Research and review the organization's recognizable slice, dimensions, period, audience and proposed stories. Record actual evidence separately from simulation assumptions.
2. Select recipes and bind product IDs, account populations, dates, units and field names to the new dataset. Declare grain and join cardinality. Do not reuse Apple names, dates or population sizes by accident.
3. Freeze mechanism parameters, lag, comparison windows, tolerances and acceptance gates before running. Keep normal failure, healthy exposed accounts, unrelated declines and competing explanations.
4. Generate baseline, each isolated mechanism and the combined state with keyed random streams. Generate feedback only from prior recorded events. Derive monetary outcomes with deterministic arithmetic.
5. Validate all tables and the final combined business. Reject failed runs without silently changing gates. Store interaction residuals separately from isolated effects. Test held-out seeds and entity renaming.
6. Freeze config/code hashes, approval declaration, checksums and private evaluations. Export only operational tables and neutral definitions. Any subsequent change creates a new release.
7. Run analyst evaluation in a separate access-controlled context, deny repository/answer-key access and test that denial. Freeze the answer before evaluator scoring. This step has not been run.

## Implemented scope versus gaps

The quality mechanism is executable independently of Apple, accepting canonical product/customer IDs and ISO dates. A renamed hospital/widget fixture verifies portability and lag boundaries. The existing margin/account/promotion mechanisms and lifecycle model remain in the Apple adapter. Their reusable recipes describe dependencies and validation, but automatic schema mapping and industry-independent execution of those adapters are not built. New industries need an adapter, not merely different labels. No additional service, agent framework or paid dependency is required; use the Python standard library. Buy/reuse database and BI hosting; own the mechanisms, economics and validation.

## Quality mechanism

Apple binding: synthetic configuration PR04-0, April–June 2025. Elevated return-line probability 45%; intermittent-failure reason and a reliability inquiry linked to the same account/purchaser. A seeded 35% of exposed accounts reduce future units to 85% after their first qualifying return plus 45 days. Others continue normal purchasing. This is a fictional configuration event, not evidence of a real Apple defect.

The current adapter iterates months, with dates unsorted within each month, so it rejects feedback lags below 32 days. This prevents a later-generated earlier order from missing eligible same-month feedback. The standalone primitive accepts arbitrary positive lags for chronologically ordered adapters. Returned quantities, refunds, 80% cost recovery and handling retain the existing accounting policy. No replacement inventory or inventory snapshots are introduced.

The operational analyst sees returns, reasons, dated inquiries and subsequent transactions. Private isolated quality effects and combined interactions remain in the answer key. Equal 90-day windows around return-plus-lag describe association, not estimated causal damage; their mix and seasonality can differ. Recent observations without complete follow-up are excluded. Return-line rate is distinct from returned-unit rate. Acquisition, concentration, promotions, unrelated account decline and margin mechanisms coexist.

Quality gates: at least 30 reliability returns, target return-line rate 25–65%, at least five exposed accounts with lower subsequent revenue in complete equal windows, at least one healthy exposed account, and one linked reliability inquiry per qualifying return. Existing combined-state gates must also pass. These are synthetic demo signal gates, not statistical causal tests. Refunds, net return costs and customer revenue changes are reported separately and never summed into a recovery estimate.

## Run

```bash
PYTHONPATH=src python -m bravura recipes
PYTHONPATH=src python -m bravura approve examples/apple/generation-bundle-v4.json --reviewer NAME --note 'Approved reviewed design' --out outputs/approval-v4.json
PYTHONPATH=src python -m bravura generate examples/apple/generation-config-v4.json --approval outputs/approval-v4.json --out outputs/apple-release-v4
PYTHONPATH=src python scripts/validate_seeds.py examples/apple/generation-config-v4.json --out outputs/held-out-v4.json
PYTHONPATH=src python -m unittest discover -s tests
```

Use new output paths; do not overwrite a released run. Approval is a local declaration, not cryptographic identity verification. All release outputs are excluded from Git.

## Verified v0.4 run

Seed 20261028, 50,000 lines, 30 months. All 24 combined story/plausibility gates pass; six generated states (baseline, four isolated, combined) pass structural/financial validation, and combined regeneration matches exactly. The two held-out seeds 20261029 and 20261030 pass the frozen story gates. All 54 tests pass, including renamed entity/date portability and exact lag boundary checks.

In the final combined target purchase cohort, 390 of 827 lines have reliability returns (47.16%), across 200 accounts with complete windows. 123 buy less in the subsequent window and 77 do not. Refunds total $4,867,404; net return cost is $2,068,010 under the declared accounting policy. These are observed totals, not incremental causal impacts. The private quality-only contrast and interaction residual are separately retained. No fresh-context blind evaluation or historical Signal rerun is claimed.
