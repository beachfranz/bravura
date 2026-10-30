# Supabase integration — v0.3 loaded and verified

The October 29 customer-dynamics release supersedes the October 28 totals below. See [current deployment and validation](customer-dynamics-v3.md). `bravura_demo` retains its connection name and 24-table structure. `hex_reader` now has explicit SELECT grants and RLS policies; Hex has successfully queried the earlier release. Historical setup details follow.

Target supplied by the user: `https://udczuujwgyqgibfkuszg.supabase.co`.

On 2026-10-28, the connected Supabase tools verified project `udczuujwgyqgibfkuszg` (`bravura`, PostgreSQL 17) and found no existing public/demo tables. Migration `create_bravura_operational_demo` created the schema. The operational release was loaded through client-supplied SQL in dependency order. Each batch committed separately; this hosted load was not a single atomic transaction. No answer key or scenario definitions were loaded. A repository link alone does not trigger imports or refreshes.

## Prepared design

Use a dedicated `bravura_demo` schema for the 24 operational tables. Keep the answer key, baseline states and scenario specifications outside this database. Money stays in integer USD cents; dates become PostgreSQL dates; identifiers remain text. Primary/foreign keys, composite account/purchaser relationships, row-level financial identities and indexes support safe loading and exploration.

Enable row-level security on every table and revoke schema/table privileges from PUBLIC, anon and authenticated. No API/client read policy is created automatically. Owner/service roles can bypass RLS, so analyst read access must be designed and tested separately. Do not hand service-role credentials to an analyst. The custom schema need not be added to Supabase's exposed API schemas for a PostgreSQL BI connection.

## Offline import preparation

```bash
PYTHONPATH=src python scripts/prepare_postgres.py outputs/apple-release-final/operational --manifest outputs/apple-release-final/answer_key/manifest.json --out outputs/postgres-import-new
```

Preparation verifies every operational file against the release manifest, rejects unexpected files, validates field types, and emits schema.sql, import.psql, the operational CSVs and an import manifest. It makes no network requests and never receives a database password. The source manifest is read only to verify operational checksums; the answer key is not copied.

Once the target project and existing schemas have been inspected, an authorized administrator can run the prepared import from its directory with psql and an independently configured connection:

```bash
cd outputs/postgres-import-new
psql "$DATABASE_URL" -X -v ON_ERROR_STOP=1 -f import.psql
```

Do not run blindly or put credentials in Git/chat. The psql export is an alternative for an empty destination; the hosted project was loaded through the connected Supabase tools.

The script creates a new schema, loads all tables in one transaction, forces deferred constraints, verifies every row count, then commits. It does not drop, truncate, replace or silently skip existing tables. If `bravura_demo` already exists, creation fails and the import must be reconciled with that existing state rather than rerun destructively. There is no automated refresh/replace workflow yet.

## Verification boundary and next steps

Offline tests check typing, privilege defaults, transaction structure, checksums, unexpected private files and no-overwrite behavior. Hosted SQL checks now verify all 24 release table counts, including 50,000 order lines, 25,000 orders, 300 accounts and 1,026 purchasers. Transactions span 2024-01-01 through 2026-06-30, totaling 830,179 units.

Financial reconciliation (integer USD cents): revenue 90,619,154,300; gross profit 23,658,733,920; contribution 23,417,515,442; refunds 1,104,611,000; net return cost 456,586,960. Revenue after returns is 89,514,543,300 and contribution after returns is 22,960,928,482. These match the validated operational release exactly. These are synthetic commercial-slice figures, not Apple's reported results.

Hosted checks found zero cost/version/date mismatches, zero shipment or line fulfillment-allocation discrepancies, zero invalid return quantities/dates, and zero unvalidated database constraints. All 24 tables have RLS enabled. Neither anon nor authenticated has schema usage. The security advisor returned only 24 informational [RLS enabled without policies](https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy) findings: intentional default-deny access pending a dedicated reader role. Owner access is available in the Supabase dashboard by selecting `bravura_demo`.

Generator validation remains the source of the broader combined-scenario checks; not every generator invariant is implemented as a database constraint. Dedicated analyst access, negative access tests, and a fresh-context analyst evaluation remain pending. The public repository contains authoring material and must not be available to the blind analyst.

## v0.4 update

The verified v0.4 combined release now occupies `bravura_demo`. All 24 table counts and sorted row-content fingerprints matched the release before activation. The previous live data is preserved in `bravura_archive_v3`, without `hex_reader` access. Current data has 50,000 lines, 1,871 returns and 8,590 account activities. Full-period sales before returns are $1,541,780,627; contribution after returns is $385,383,360.63. Supersedes earlier totals.

The two operational queries in `sql/returns-investigation.sql` execute successfully against the live data. Hex application refresh is separate from database activation. Blind access-negative testing remains not run. Security advisors report only the existing 24 informational missing-policy notices for the intentionally inaccessible rejected v3 staging schema.
