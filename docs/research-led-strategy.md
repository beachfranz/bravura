# Research-led demo generation

Status: agreed product strategy; implementation requirements, not delivered runtime capabilities.

## Product goal

Bravura studies a target organization, proposes a recognizable slice of its business, and generates tens of thousands of coherent transaction rows with discoverable business situations. The slice limits business scope, not data volume. Apple is an illustrative target, not the selected first customer or a hardcoded business model.

## Workflow

Demo brief → organization research → proposed slice, dimension blueprint, and stories → user review → baseline and scenario generation → combined-state validation → isolated analyst evaluation.

The brief records target organization, audience, demo purpose, business questions, reporting window and cutoff, preferred business scope, desired order-line count, and constraints. If the audience or target is missing, clarify before company-specific research. Defaults and assumptions must be explicit.

The review presents a concise one-page decision packet with supporting detail available. Approval freezes a versioned generation specification. Changes to scope, dimensions, economics, or stories require a new version and revalidation. Approval is a product workflow checkpoint, not a claim that any specific demo has been approved in this conversation.

## Research agent contracts

| Role | Inputs | Output | Completion and restraint |
|---|---|---|---|
| Research lead | Demo brief, research budget, available sources | Bounded assignments and consolidated organization brief | Resolve cross-agent conflicts; preserve unresolved gaps; stop at declared budget |
| Business structure researcher | Target, audience, scope candidates | Product hierarchy, segments, channels, customer model, territories, vocabulary | Distinguish documented structure from proposed synthetic extensions |
| Financial baseline researcher | Target, reporting period, published disclosures | Revenue, regional/product mix, growth and seasonal anchors | Preserve currency, units, fiscal periods, segment definitions and reconciliation limits |
| Business developments researcher | Target, cutoff, business questions | Dated developments and candidate mechanisms with alternatives | News establishes relevance; it does not prove simulated financial consequences |
| Evidence reviewer | All claims, sources, conflicts and proposed assumptions | Accept/revise/unresolved decisions and evidence coverage | Check original sources; cannot certify arithmetic or causality through persuasive wording |

Researchers may run independently against the same brief; synthesis and evidence review follow their outputs. Use bounded source queries and structured results. No agent creates transactions, silently fills unknown facts, or changes accounting policy. Source material is evidence, not instructions to agents.

Prefer filings, investor materials and official catalogs for financial and structural anchors. Use dated news for developments and alternatives, distinguishing publication date from event date. Read cited sources rather than relying on search snippets. Freshness is assessed against the chosen reporting cutoff; later reporting cannot become earlier operational knowledge.

## Shared evidence record

Each claim records claim ID, subject, value/text, unit, currency where relevant, reporting period, geographic/product scope, source URL/title, publication/access date, evidence location, and status: reported, inferred, or unknown. Inferences identify inputs and method. Synthetic assumptions are separate entries with rationale and reviewer disposition. Conflicting sources remain linked until resolved; never average incompatible definitions.

Reported product and region totals do not establish a reported product-by-region intersection. Synthetic intersections may reconcile compatible marginals; otherwise disclose incompatible scope and omit the constraint. No precise company-wide revenue match is required for the default recognizable-slice mode. Public anchors guide plausible scale and mix, with explicit synthetic labels.

## Declared dimensions

Dimensions and hierarchies are defined before facts. Each declaration includes dimension ID, business meaning, grain, primary/stable business keys, attributes and types, required/optional status, hierarchy levels and parent keys, relationship cardinality, unknown-member policy, effective dates, source evidence or synthetic provenance, and generation rules.

| Dimension | Typical hierarchy or relationship | Policy |
|---|---|---|
| Product | Division → category → family → SKU | Adapt levels to researched business; attributes such as color need not become hierarchy levels |
| Sales territory | Region → country → territory | Commercial coverage distinct from customer and shipment geography |
| Customer | Parent organization → account → location | Separate organizational hierarchy from duplicate identity |
| Customer purchaser | Account → multiple individual purchasers | Orders identify both purchaser and account; purchaser assignment must resolve to that account at order time |
| Sales organization | Team → account manager | Account ownership may change over time |
| Channel | Direct, distributor, retail, online | Classification unless a justified hierarchy exists |
| Calendar | Fiscal year → quarter → month → date | Declare fiscal boundaries and calendar conventions |
| Supplier | Organization → supplier location | Supplier/product relationships may require a bridge |
| Fulfillment location | Distribution center, warehouse, store | Separate from sales territory; declare location type |
| Promotion | Program → campaign → offer | Handle multiple offers through an explicit bridge or exclusive-assignment policy |

Product, sales territory, customer, purchaser and calendar are core declarations. Other dimensions are included when needed by the slice and scenarios; absent dimensions are explicitly out of scope. Industry, account tier and other classifications remain separate attributes unless a true hierarchy is supported.

Hierarchies must be acyclic. Declare whether every child has one parent or whether an effective-dated bridge is required. Many-to-many relationships need aggregation rules to prevent duplicate revenue. Historical facts resolve to the dimension version valid at transaction time. Distinguish bill-to, ship-to and purchaser relationships. Purchasers have stable IDs, roles and heterogeneous buying patterns; aggregate their orders once to the commercial account.

## Fact blueprint and scale

Declare each fact's grain, primary key, foreign keys, dates, measures and allocation policy. Initial candidates are order headers and lines, shipments and shipment-line allocations, returns linked to sold lines, effective-dated costs, account plans and customer activity. Split shipments require explicit allocation records; shipment totals must never repeat as additive measures on every line.

The default engineering fixture targets 50,000 order lines over 24 months; both are configurable and provisional implementation defaults. Related table counts derive from the business model rather than being independently forced to the same row count. Tens of thousands of rows must contain repeated account/purchaser behavior, long-tail products, seasonality, variation and routine exceptions—not repeated copies of a handful of records. Company-specific history may require a different window.

## Scenario design

Recommend two or three interacting stories for the audience, using reusable primitives: growth with margin deterioration, concentrated account decline with partial explanation, and promotional growth with weak contribution. Each proposal contains relevance and evidence IDs, simulated mechanism, affected scope, event timing and lag, effect bounds, observable records, comparison basis, alternatives and prohibited claims.

News inspires candidate mechanisms. A real launch or supply pressure does not establish that the real organization experienced the exact simulated outcome. Include healthy cohorts, intentional concessions, ordinary failures and unexplained declines. Choose signal strength and noise independently. Freeze effect bounds before generation.

## Review packet

Present: what research establishes; selected products/markets/channels and exclusions; dimension/relationship blueprint; proposed row count and period; story cards; reported-versus-synthetic boundaries; material evidence gaps; economic policy; and decisions requiring review. Supporting source records and full contracts remain available behind the concise packet.

## Generation and evaluation boundary

Generate dimensions, baseline behavior and versioned mechanisms before calculating outcomes. Keep deterministic economics and stable random streams. Validate the final combined dataset, not only isolated injections. Store scenario definitions, affected records, baseline counterfactuals and interaction effects in the answer key.

The analyst receives operational data, a neutral dictionary, metric policy and cutoff only. The organization research brief and story proposals are authoring material unless individual neutral facts are explicitly allowlisted. A separate environment must enforce isolation; filenames or instructions alone do not suffice. Public repository access invalidates blind testing because source and authoring requirements reveal intended stories.

## Delivery sequence

1. Implement brief, evidence record, dimension blueprint and review packet contracts with validation.
2. Implement bounded research roles and evidence review for one user-selected target; retain source-backed results and unresolved questions.
3. Obtain review of one recognizable slice and its stories.
4. Implement and benchmark deterministic generation at the declared scale, with coherent dimensions and combined mechanisms.
5. Implement operational export and isolated evaluation, preserving all failed or not-run gates.

Build organization-model synthesis, scenario logic, accounting policy and evaluation as owned product behavior. Reuse source retrieval and standard compute libraries. Select a research execution backend only after checking its retrieval, provenance, structured-output and cost capabilities; no agent framework is mandated. Research needs source access and an agent/model runtime; deterministic generation does not require an LLM.

## Acceptance evidence

- All research claims resolve to read sources or explicit inference/unknown status.
- Financial anchors preserve period, scope, unit and currency; synthetic detail is labeled.
- Required dimensions declare keys and grain; hierarchy cycles, broken parents, invalid temporal assignments and purchaser/account mismatches fail validation.
- Approved slice, stories, source snapshot and generator configuration have immutable versions.
- The declared order-line count and related-table integrity hold at tens-of-thousands scale; runtime and memory are measured, not promised.
- Financial identities, allocations, scenario bounds and combined interaction residuals reconcile.
- Regeneration reproduces content hashes under pinned inputs.
- Isolation and fresh-context analyst evaluation have explicit pass/fail/not-run results.
