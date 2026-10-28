# Bravura Narrative Generation Playbook

Version 1.0 · October 28, 2026 · Authoring guidance derived from Signal

Bravura should generate commercially plausible business situations that an analyst can discover, investigate and explain from operational evidence. A convincing story is an outcome of coherent data generation, not a paragraph embedded in a dataset.

This playbook recommends a reusable generation contract. It does not assert that Bravura already implements these capabilities. The included Signal package is a worked reference, not a universal industry model. Its historical validation reports and analyst outputs are preserved; the generator and analyst were not rerun for this handoff.

## 1. Define the decision before generating rows

Start each scenario with the decision a business user must make: recover margin, redesign a promotion, investigate account decline, or improve a service process. Specify the audience, comparison period, reporting cutoff, economic metric and action constraints. Then work backward to the operational evidence required.

A useful narrative has five ingredients:

1. A material change or tension, such as rising revenue and falling contribution.
2. A concentrated population that explains where the issue matters.
3. Evidence spread across related tables that requires investigation.
4. At least one credible alternative explanation or unresolved question.
5. A proportionate next action with an owner and a way to learn more.

Do not make every anomaly harmful, every discount excessive or every decline explainable. Include healthy growth, intentional concessions, stable populations and ordinary operational failures.

## 2. Generate mechanisms before outcomes

Construct a baseline business with repeat purchasing, heterogeneous accounts, product economics, seasonal variation and routine returns and service problems. Apply versioned events to that baseline, then derive transactions and their financial results.

Examples of mechanisms include a supplier cost increase, a promotion changing demand and mix, or a service disruption preceding weaker account demand. Do not independently manufacture the order, shipment and return tables to hit unrelated totals.

Use explicit dependency order: business calendar and entities → product costs and commercial terms → demand and orders → fulfillment → returns and credits → financial measures → operational context → private evaluation outputs. If the model includes feedback from service to future demand, encode that time lag explicitly.

Record the seed, generator version, dependency versions, source checksum, configuration and output checksums. The historical Signal README's example seed differs from the packaged validation report's seed; a copyable command is not sufficient provenance. Regeneration must use the configuration of the actual release.

## 3. Use a scenario contract

For every scenario, record the following in an authoring-only specification. The companion JSON template provides a starting structure, not an executable generator schema.

| Contract field | Required content |
|---|---|
| Business decision | Audience, question, action owner and constraints |
| Scope | Entity selection, grain, start/end dates and reporting cutoff |
| Mechanism | Events, dependency order, parameter ranges and lag assumptions |
| Baseline | No-event behavior, seasonality and ordinary variation |
| Operational evidence | Fields, joins and time sequences the analyst can inspect |
| Economics | Metric definitions, expected direction, magnitude bounds and reconciliation tolerance |
| Comparisons | Prior period, plan, peer cohort or private counterfactual; never conflate them |
| Alternatives | Competing explanations and the evidence needed to distinguish them |
| Permitted conclusions | Observable facts, arithmetic attribution and supported hypotheses |
| Prohibited conclusions | Unsupported intent, causal claims or extrapolated benefits |
| Interaction policy | Shared populations, event order, joint effects and residual treatment |
| Evaluation | Detection, evidence, quantification, restraint and action criteria |
| Publication boundary | Operational allowlist and authoring/evaluator-only assets |

Choose effect ranges before generation. If a completed run misses them, fix the generator or reject the run; do not rewrite expected answers to disguise an accidental outcome.

## 4. Preserve coherent entities and time

Model organizations separately from contacts. Sales belong to a commercial account even when several people place orders. Retain stable keys through orders, contacts, account plans and activity. Signal's worked example includes single-buyer Consumer households and multiple-buyer Corporate and Small Business accounts; other industries need their own hierarchy.

Declare table grain and join cardinality. A shipment cost must not be repeated on every line when aggregating orders. Return quantities must respect quantities sold. Cost versions must resolve uniquely on the transaction date. Events cannot refer to unavailable products or accounts before acquisition unless explicitly modeled.

Use one reporting cutoff. A return or service note recorded later must not inform an earlier analysis. In more advanced simulations, retain both event time and knowledge time. Future outcome measurement should use a later snapshot, not information smuggled into the initial briefing.

## 5. Make the economics deterministic

Use tested calculations for prices, costs, allocations and reconciliation. Language models can propose scenarios and write explanations; they should not be the accounting engine.

Signal's reference definitions are:

```text
net_unit_price = list_unit_price × (1 − discount_rate)
net_sales_before_returns = quantity × net_unit_price
product_cost = quantity × effective_standard_unit_cost
gross_profit_before_returns = net_sales_before_returns − product_cost
contribution_before_returns = gross_profit_before_returns
                              − allocated_fulfillment_cost − variable_program_cost
net_return_cost = refund_amount + restocking_cost − recoverable_inventory_value
net_revenue_after_returns = net_sales_before_returns − refund_amount
contribution_after_returns = contribution_before_returns − net_return_cost
```

These are reference policies, not universal accounting rules. Declare how discounts, credits, rebates, freight, tax, returned inventory and missing costs are treated. Do not deduct a refund twice or add an inventory recovery twice. Allocate shared costs once and reconcile allocations to their source totals. Define rounding and zero-denominator behavior. Missing cost is unknown, not zero.

Maintain distinct fields for historical deterioration, modeled opportunity, approved action value and realized benefit. A synthetic causal effect is available to the evaluator because the generator knows the mechanism. An operational analyst still needs evidence sufficient for its claim; it cannot call a prior-year benchmark gap causal lift.

## 6. Reuse the three Signal story patterns

### Growth concealing margin deterioration

In Furniture, cost increases, mix changes, fulfillment and smaller discount effects jointly weaken contribution. The packaged executive briefing reports H2 year-over-year sales up $26,763 and contribution down $19,516 to negative $9,009. These are observed comparisons, not isolated scenario effects.

The transferable pattern is a headline that looks healthy until costs and mix are examined. Provide effective-dated cost history, product-level economics and fulfillment evidence. Avoid making a single discount field explain everything. An appropriate action considers supplier terms, assortment, pricing constraints and expedite policy together.

### Concentrated account decline with partial explanation

The West story focuses on Oakridge Advisory and Juniper Analytics. Both miss plan; only Juniper has unresolved late-delivery evidence. Oakridge's cause remains unknown. Multiple buyer contacts roll up to each organization.

The transferable pattern is concentration plus different evidence strength. Provide routine account plans and activity for a normal comparison population, not only the two affected accounts. Support targeted recovery and discovery. Do not imply regional market weakness, competitor loss or definitive churn without supporting evidence.

### Growth with weak promotional economics

The Technology promotion combines volume, lower realized price, program cost, returns and expensive fulfillment. The packaged briefing reports $92,347 sales after returns and negative $4,607 contribution for the promoted cohort. Its 23.7% return-line rate is compared with 1.3% for nonpromoted sales of the same products; this denominator is not the entire nonpromotion population.

The transferable pattern is a tradeoff whose outcome differs by cohort. Include normal background returns, profitable and unprofitable populations where appropriate, and comparable nonpromoted observations. A reasonable action is to investigate cohorts and test redesigned terms. Benchmark differences do not prove incremental promotion effects.

### Do not mix comparison bases

The historical validation report also gives isolated injection effects: Furniture +$5,480 sales/−$18,585 contribution; Technology +$17,510 sales/−$17,425 contribution; West −$9,632 sales/−$4,324 contribution. Those values answer different questions from the executive briefing's year-over-year, plan and benchmark comparisons. Keep metric, population, period and comparison basis attached to every number.

## 7. Engineer realism and analytical difficulty

Distribute routine returns, late shipments, activity and account plans across unaffected entities and historical periods. Avoid special flags that identify only the intended discovery population. Keep operational names neutral and legitimate business reason codes useful without encoding the conclusion.

Control signal strength, noise, entity concentration, time lag, data completeness and number of competing mechanisms independently. Useful difficulty levels are: a clear single mechanism; interacting mechanisms with good evidence; overlapping populations and ambiguous explanations; and incomplete evidence requiring abstention.

Difficulty must not come from broken financial identities. Introduce missing or conflicting data only as explicit data-quality scenarios with their own expected analyst behavior. A missing-cost scenario should block unsupported profitability conclusions.

## 8. Validate scenarios together

An isolated scenario can work while the combined business tells a different story. Generate baseline, isolated scenarios and the final combined state. Recalculate detectable effects and priorities from the combined state.

For overlapping scenarios, store affected record sets and use a declared counterfactual attribution method. Joint effects need not equal the sum of isolated effects; report the difference as interaction/residual unless an explicit allocation method is chosen. Never count the same economic component twice.

Signal's historical report records 35 queue memberships across 31 unique organizations. Queue membership is an investigation trigger, not a cause. Size the union of accounts separately from queue totals, and do not add sales exposure, refunds and contribution loss into one benefit figure.

## 9. Separate authoring from blind evaluation

Maintain three access scopes:

| Scope | Allowed assets |
|---|---|
| Bravura authoring | Generator, scenario contracts, baseline, private truth, prior outputs and tests |
| Blind analyst | Released operational tables, neutral dictionary, metric policy and reporting cutoff |
| Evaluator | Frozen analyst output plus private truth, expected evidence and scoring rules |

Build analyst releases from an explicit allowlist. Exclude generator code, baseline counterfactuals, scenario specifications, audits, expected answers, briefings and evaluation results. Enforce the boundary through file placement and tool permissions, not a prompt asking the analyst to ignore accessible answers. Use a fresh context that has never seen the authoring materials.

Scan operational column names, values, notes, filenames and metadata for answer leakage. A clean column scan alone does not prove the entire analyst environment is isolated. Original source audit fields can also reveal injected changes; the current Signal validation report records their exclusion from operational orders even though the earlier specification proposed retaining them.

## 10. Release gates and evidence

| Gate | Required result |
|---|---|
| Structural integrity | Unique keys, valid foreign keys, declared grain and valid cardinalities |
| Temporal integrity | Valid event sequence, unique effective costs and no post-cutoff evidence |
| Financial integrity | Identities and allocations reconcile within declared tolerances |
| Plausibility | Distributions and baseline rates stay within configured business assumptions |
| Scenario integrity | Intended effects survive the combined run within specified bounds |
| Reproducibility | Same pinned inputs and seed reproduce content checksums; volatile metadata is handled explicitly |
| Isolation | Analyst release contains only allowlisted assets; access tests reject private paths |
| Discoverability | A fresh analyst identifies material findings from operational evidence |
| Restraint | Unsupported causal and intent claims are penalized; justified uncertainty is rewarded |

Score detection and prioritization separately from explanation quality. Track precision/recall, impact error, driver ranking, evidence coverage, unsupported claims and action quality. Quantification must compare like with like: an observed year-over-year change is not an estimate of an isolated intervention effect. Record sample size and scoring thresholds before evaluation.

Retain run metadata, validation results, analyst findings, calculation trace and evaluation results together. Test new seeds, different entity names and held-out periods so success does not mean memorizing one demo. A polished briefing alone is not proof the generator works.

## 11. Bravura implementation sequence

1. Map this contract to Bravura's existing schema, generator and user workflow. Preserve working capabilities and identify gaps.
2. Implement one end-to-end scenario with baseline, mechanism, coherent tables, private truth and release validation.
3. Add a second interacting scenario and demonstrate combined-state reconciliation.
4. Add ambiguous and benign cases; test abstention and false positives.
5. Create separate authoring and operational export paths with enforced access boundaries.
6. Run fresh-context evaluations over varied seeds and retain inspectable evidence.

Build Bravura's narrative contracts, mechanism composition, economic policies and release checks as owned product logic. Reuse standard table-generation, validation and analytical libraries where they fit. Do not adopt Signal's orchestration stack or a vendor dependency merely because it appears in a reference document; those are separate product choices.

## 12. Source precedence and limitations

For the worked example, use actual packaged tables and run metadata for what exists, the packaged analyst outputs for what was reported, and specifications for intended behavior. Resolve discrepancies explicitly.

The September 7 package has ten operational CSVs including organizations and account plans; it does not include inventory snapshots. The earlier synthetic specification proposes inventory and targets. The standalone scenario audit predates the latest package and is included as a historical QA example, not an authoritative reconciliation of the latest run. Signal's OpenAI mode is documented as implemented but unexecuted in that build. The broader product specification is proposed scope.

The bundle includes the original package unchanged, its synthetic specification, the historical scenario audit, the current project brief/README/product specification, and a source manifest. Refer to those assets for detail; treat this playbook as the Bravura adaptation guidance.
