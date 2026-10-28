# Supabase integration — prepared, not applied

Target supplied by the user: `https://udczuujwgyqgibfkuszg.supabase.co`.

Supabase installation is confirmed. At preparation time, its project/schema/SQL tools were not exposed to this session. No remote tables have been inspected or created, and no data has been loaded. A repository link alone does not provide database credentials or trigger this import.

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

Do not run blindly or put credentials in Git/chat. The application should ultimately use the connected Supabase tools or an authenticated loader; this psql export is a prepared fallback, not a completed connection.

The script creates a new schema, loads all tables in one transaction, forces deferred constraints, verifies every row count, then commits. It does not drop, truncate, replace or silently skip existing tables. If `bravura_demo` already exists, creation fails and the import must be reconciled with that existing state rather than rerun destructively. There is no automated refresh/replace workflow yet.

## Verification boundary and next steps

Offline tests check typing, privilege defaults, transaction structure, checksums, unexpected private files and no-overwrite behavior. PostgreSQL execution has not been tested in this session. Generator validation remains the source of cross-row temporal/economic checks; not every generator invariant is implemented as a database constraint.

Once SQL tools are available: verify project identity; list existing schemas/tables/migrations; apply the reviewed schema through the supported migration path; load the operational tables; verify 50,000 order lines, 25,000 orders, 300 accounts and 1,026 purchasers plus all other manifest counts; reconcile financial totals and joins; then establish read-only access appropriate to the analyst. No blind-analysis isolation claim is made until that access is tested.
