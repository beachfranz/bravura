# Apple generation release v0.2

The user approved the Apple slice and stories with “Looks great. Run with it.” The implementation completes the scoped catalog and numerical policies under that instruction. `examples/apple/generation-bundle.json` preserves the approved scope and binds `generation-config.json` by SHA-256. Original research remains in `bundle.json`.

## Implemented scope

A deterministic local generator, tested at 50,000 order lines / 25,000 two-line orders, over January 2024–June 2026. It produces 300 fictional accounts with 2–5 purchasers each; 24 synthetic configuration SKUs across eight selected Apple generations; declared product-category/family/version tables; customer parents/locations; territories; channels; sales reps; suppliers; fulfillment locations; calendar; costs; promotions; shipments; allocations; returns; plans; activity.

Version 0.2 is an Apple-specific first slice, not an arbitrary-company generator. It enforces the current dates, cutoff, account count and core cohorts. Row count, seed and numerical mechanism settings are configurable within validation bounds and require a matching approved configuration hash.

Public catalog sources and launch lower bounds are in generation-config.json. Model generations: iPhone 15/16; MacBook Air M2/M3/M4; iPad Air M1/M2/M3. All were checked against official Apple launch announcements. Exact country-specific availability is not independently established. Later generations are deliberately omitted; synthetic reseller sell-through allows selected older models through June 2026. Configuration bands, business prices, cost ratios and supply assumptions are invented, not actual Apple SKUs or economics.

## Run

```bash
export PYTHONPATH=src
python -m bravura approve examples/apple/generation-bundle.json --reviewer "Your name" --note "Your actual decision" --out outputs/apple-approval.json
python -m bravura generate examples/apple/generation-config.json --approval outputs/apple-approval.json --out outputs/apple-release-new
python -m unittest discover -s tests -v
python scripts/validate_seeds.py examples/apple/generation-config.json --out outputs/held-out-seeds.json
```

The approve command must represent an actual decision; it does not ask a model to approve itself. In the delivered run, approval records the user's instruction above and discloses implementer-completed details. The local declaration is not cryptographic identity authentication. Generation refuses a changed config hash or changed scope.

## Economics and mechanisms

- All money is integer USD cents. Net unit price, program cost and inventory recovery use half-up rational rounding. Gross profit and contribution are distinct. Largest-remainder allocation conserves shipment totals exactly.
- Baseline repeat purchasing has monthly seasonality, heterogeneous quantities, customers, buyers, products, ordinary returns and late deliveries. Corresponding months deliberately share preferences to stabilize comparison; this is controlled demo realism, not a fitted demand model.
- Margin pressure changes effective product costs for US/UK orders from January 2026, increases premium-configuration mix and expedite usage.
- Purchasing declines at two mainland-China accounts after March 3, 2025. Only one receives an unresolved delivery pattern beginning February; the other retains ordinary background activity. No competitor or churn explanation is inserted.
- MacBook Air refresh offers run April–June 2025 and repeat April–June 2026. Growth-tier accounts in US/UK/India qualify. Direct and reseller terms differ, creating profitable and loss-making cohorts. The repeat is an explicit implementation choice to overlap with 2026 margin pressure.
- Baseline and isolated/combined states share keyed random draws. Quantities and mix change without changing the 50,000 line count. One shipment per order, at most one return per line, fixed USD reporting and no inventory constraints are v0.2 simplifications.
- Freeze effect bounds in configuration before release. A miss rejects the run; do not rewrite bounds to hide it. The delivered default passed its first full combined scenario run with the original numerical bounds.

## Evidence and comparison policies

The answer key stores baseline and each isolated state's line economics, combined state, affected record sets, scenario comparisons and an explicit interaction residual. All monetary values are cents. Private intervention contrasts are computed against baseline; they are never labeled observed YoY changes.

US/UK observations compare H1 2025 vs H1 2026 after returns. Account observations compare March 3–December 31 across 2024/2025 before returns. The promotion private unit comparison uses identical eligible line IDs. Promotional cohort contribution covers both annual offers. Calendar periods are not Apple's fiscal periods. Unknown costs fail validation rather than becoming zero; missing-cost scenarios are not yet generated.

## Release checks

Baseline, three isolated states and combined state pass uniqueness, references, product hierarchy, account/purchaser and location ownership, positive costs, effective-date non-overlap, launch-date checks, shipment/return chronology, exact financial identities and allocations, plans known before their period, and 30 populated months. Combined scenario gates retain the original proposed ranges, healthy peers, both promotion outcomes and nonzero interaction.

The combined state is generated twice and compared in full. Operational files have content checksums. Code, configuration, approval and Python-version provenance accompany the answer key. `runtime.json` is volatile and deliberately not part of the operational reproducibility claim. The ZIP metadata is fixed; the operational ZIP is deterministic for pinned inputs. Full answer-key archive bytes can differ due to measured runtime.

Two additional seeds, 20261029 and 20261030, passed combined structural/financial checks and frozen scenario bounds. This is a small seed test, not a claim of generalization to all seeds or other organizations. The unit suite adds corruption tests for mismatched purchaser, missing cost, doubled allocation, excessive returns, post-cutoff activity and broken hierarchy.

## Deliverables and isolation limits

`operational.zip` contains only allowlisted business CSVs, a neutral dictionary and a synthetic-data notice. The product dimension excludes baseline-cost audit values. `answer_key.zip` includes the generator parameters, approved design, private states, affected records, comparisons, validation and provenance. The enclosing delivery ZIP includes both plus an authoring overview.

Never provide the enclosing ZIP, answer key, overview, source repository or design packet to a blind analyst. ZIP allowlist and negative private-path tests pass, but they do not enforce a separate analyst environment. Full filesystem/tool isolation and fresh-context analyst evaluation are **not run**. Build that boundary before claiming discoverability in a blind test.

## Remaining work

Live research/model integration, an interface for alternate target organizations, richer fiscal calendar handling, explicit new/lost account generation, split shipments, inventory, automated statistical plausibility calibration, and isolated analyst execution remain outside this release. No actual company customer data or realized business benefit is claimed.
