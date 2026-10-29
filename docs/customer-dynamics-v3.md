# Customer dynamics revision (authoring only)

The October 29 audit found that v0.2 forced all 300 customers to purchase monthly, assigned a single 2023 acquisition date, and did not create material account concentration. That release supports a profit squeeze and local account decline, not acquisition masking inactivity or concentration risk.

## Implemented revision

The opt-in `customer_dynamics` configuration preserves the v0.2 path when absent. The 24-table schema, integer-cent economics, 50,000 lines, 30-month calendar and three existing scenario mechanisms remain. No new runtime dependencies or purchased service is required.

The structural baseline now includes 40 accounts acquired in two staggered annual cohorts, ramp-up, 20 accounts that cease purchasing in late 2025, 10 with a temporary purchasing hiatus, and irregular ordering for other accounts. Ten large accounts and three growing anchor accounts create dependence on customers and their parent groups. New accounts have an additional commercial discount; operational discounts and acquisition dates expose the evidence without exposing private lifecycle flags. Purchase inactivity is not an operational assertion of confirmed churn.

These structural dynamics are present in baseline, isolated and combined states. Existing private intervention contrasts still apply only to margin, account decline and promotion. No causal estimate of customer acquisition, dormancy or concentration is claimed. Fixed total order counts cause demand reallocation when accounts are unavailable; this is a bounded commercial-slice simulator, not an unconstrained market-demand forecast. Account plans are synthetic advance estimates, not fitted to realized purchases.

## Combined release gates

`customer_audit.py` builds exact before-return revenue and contribution bridges for calendar 2025/2024 and H1 2026/2025. Each account belongs to exactly one comparison cohort: newly acquired, returning/outside prior window, inactive, retained declining or retained growing. Both bridges reconcile exactly to the overall change. Newness uses acquisition date, not merely first appearance in a truncated window.

Additional gates require: revenue growth with falling contribution in H1; top-ten share between 25% and 65% and rising; at least ten acquired and ten inactive accounts; deterioration among previously large accounts; and lower contribution margin for newly acquired customers. Existing scenario, financial, temporal, export and reproducibility gates remain.

Candidate 1 (large-account scale 7x) passed the selected seed but failed the concentration cap on both held-out seeds. It was rejected. Candidate 2 reduces account scale to 5x without relaxing any gates. Retain failed-run evidence outside Git with other evaluator material.

## Boundaries

These records are synthetic, not Apple financials. Calendar years are not Apple fiscal years. Do not give this document, generator, configuration, audit or old answer-bearing Hex thread to a blind analyst. Full isolated fresh-context evaluation is still not run. Hex dashboard authoring is not a blind evaluation.

## Verified release and deployment

Candidate 2 is live in `bravura_demo`. All 50 tests pass; the selected seed and two held-out seeds (20261029, 20261030) pass the combined story gates; same-input combined regeneration matches exactly. The hosted 24-table contents match the validated CSVs using row counts and sorted row-content fingerprints (MD5 used for transfer-error detection, not security). Dataset totals: 50,000 order lines, revenue 158,741,063,800 cents and contribution 40,636,154,487 cents across the full 30-month window.

H1 2026 versus H1 2025, before returns: revenue $332,291,140 versus $301,152,509; contribution $76,051,471.28 versus $77,610,347.59. Twenty newly acquired accounts bring $4,938,688 revenue and $812,520.48 contribution. Twenty inactive accounts previously contributed $10,815,106 revenue and $2,794,366.02 contribution. Active count stays 280. Top-ten account revenue share rises from 53.68% to 56.19%; parent top-ten share rises from 58.51% to 60.79%.

Deployment used a separate staging schema, followed by an atomic schema rename. `bravura_archive_v2` preserves the prior release, with schema and table access revoked from `hex_reader`. The rejected first candidate's partial staging schema `bravura_stage_v3` remains restricted, with no reader grants. No data was silently overwritten. Live Hex SELECT verification follows through the connected application; full blind isolation remains untested.

Reproduction configuration: `examples/apple/generation-config-v3.json`, reviewed bundle `examples/apple/generation-bundle-v3.json`. Approval record and run evidence are evaluator-only under `outputs/apple-release-v3-r2/answer_key`. The approval records the user's explicit authorization and the implementation-selected parameters; it is not a cryptographic identity signature.
