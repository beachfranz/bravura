"""Versioned, dependency-free validation for the first authoring milestone.

These are executable v1 contracts, separate from the reference design template.
Validation establishes structural consistency, not real-world source truth.
"""
from datetime import date, timedelta
from calendar import monthrange
from hashlib import sha256
import json
import re
from urllib.parse import urlparse


class Invalid(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Invalid(message)


def obj(value, where):
    require(isinstance(value, dict), f"{where}: expected object")
    return value


def text(value, where):
    require(isinstance(value, str) and bool(value.strip()), f"{where}: required text")
    return value


def seq(value, where, minimum=0):
    require(isinstance(value, list) and len(value) >= minimum,
            f"{where}: expected list with at least {minimum} items")
    return value


def texts(value, where, minimum=1):
    for item in seq(value, where, minimum):
        text(item, where)


def day(value, where):
    text(value, where)
    try:
        result = date.fromisoformat(value)
    except ValueError as exc:
        raise Invalid(f"{where}: expected ISO date") from exc
    require(result.isoformat() == value, f"{where}: expected YYYY-MM-DD")
    return result


def integer(value, where, low, high):
    require(type(value) is int and low <= value <= high,
            f"{where}: integer between {low} and {high} required")


def keyed(items, where):
    result = {}
    for item in seq(items, where):
        obj(item, where)
        key = text(item.get("id"), f"{where}.id")
        require(re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_-]*", key), f"{where}: invalid ID {key}")
        require(key not in result, f"{where}: duplicate ID {key}")
        result[key] = item
    return result


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def brief(data):
    obj(data, "brief")
    require(data.get("schema_version") == 1, "brief: schema_version must be 1")
    for key in ("target", "audience", "purpose"):
        text(data.get(key), f"brief.{key}")
    texts(data.get("questions"), "brief.questions")
    texts(data.get("constraints"), "brief.constraints", 0)
    require(data.get("mode") == "recognizable_slice", "brief: unsupported mode")
    start = day(data.get("start_date"), "brief.start_date")
    end = day(data.get("end_date"), "brief.end_date")
    cutoff = day(data.get("reporting_cutoff"), "brief.reporting_cutoff")
    require(start <= end <= cutoff, "brief: start <= end <= cutoff required")
    require(start.year <= 9997, "brief: start year cannot support two years of history")
    # Inclusive end: Jan 1, 2024 through Dec 31, 2025 is two full years.
    anniversary = date(start.year + 2, start.month,
                       min(start.day, monthrange(start.year + 2, start.month)[1]))
    require(end >= anniversary - timedelta(days=1),
            "brief: at least two full years (24 months) of transaction history required")
    integer(data.get("order_lines"), "brief.order_lines", 10000, 1000000)
    budget = obj(data.get("budget"), "brief.budget")
    integer(budget.get("sources_per_role"), "sources_per_role", 1, 30)
    integer(budget.get("timeout_seconds"), "timeout_seconds", 1, 300)
    return data


def research(data, spec):
    obj(data, "research")
    sources = keyed(data.get("sources"), "sources")
    claims = keyed(data.get("claims"), "claims")
    cutoff = day(spec["reporting_cutoff"], "cutoff")
    for key, source in sources.items():
        for field in ("title", "url", "snapshot_text"):
            text(source.get(field), f"source {key}.{field}")
        parsed = urlparse(source["url"])
        require(parsed.scheme in {"http", "https"} and parsed.netloc,
                f"source {key}: HTTP(S) URL required")
        published = day(source.get("published_date"), f"source {key}.published_date")
        accessed = day(source.get("accessed_date"), f"source {key}.accessed_date")
        require(published <= cutoff, f"source {key}: published after cutoff")
        require(published <= accessed, f"source {key}: access precedes publication")
    for key, claim in claims.items():
        for field in ("statement", "scope"):
            text(claim.get(field), f"claim {key}.{field}")
        status = claim.get("status")
        require(status in ("reported", "inferred", "unknown"), f"claim {key}: invalid status")
        require(day(claim.get("period_start"), key) <= day(claim.get("period_end"), key) <= cutoff,
                f"claim {key}: invalid period")
        evidence = seq(claim.get("evidence"), f"claim {key}.evidence")
        for support in evidence:
            obj(support, key)
            sid = support.get("source_id")
            require(isinstance(sid, str) and sid in sources, f"claim {key}: unknown source")
            quote = text(support.get("excerpt"), f"claim {key}.excerpt")
            require(quote in sources[sid]["snapshot_text"], f"claim {key}: excerpt not in source snapshot")
            text(support.get("location"), f"claim {key}.location")
        if status == "reported":
            require(evidence, f"claim {key}: reported fact needs source evidence")
        if status == "inferred":
            text(claim.get("method"), f"claim {key}.method")
            inputs = seq(claim.get("input_claim_ids"), f"claim {key}.input_claim_ids", 1)
            require(all(isinstance(x, str) and x in claims and x != key for x in inputs),
                    f"claim {key}: invalid inference inputs")
            require(all(claims[x].get("status") != "unknown" for x in inputs),
                    f"claim {key}: unknown claim cannot support inference")
        if status == "unknown":
            text(claim.get("gap"), f"claim {key}.gap")
            require(claim.get("value") is None, f"claim {key}: unknown has a value")
        if claim.get("value") is not None:
            text(claim.get("unit"), f"claim {key}.unit")
            if claim["unit"] == "money":
                require(isinstance(claim.get("currency"), str) and
                        re.fullmatch("[A-Z]{3}", claim["currency"]), f"claim {key}: currency required")
        for conflict in seq(claim.get("conflicts_with", []), key):
            require(isinstance(conflict, str) and conflict in claims and conflict != key,
                    f"claim {key}: unknown conflicting claim")
    visiting, visited = set(), set()
    def visit(key):
        require(key not in visiting, "claims: circular inference")
        if key in visited:
            return
        visiting.add(key)
        if claims[key]["status"] == "inferred":
            for parent in claims[key]["input_claim_ids"]:
                visit(parent)
        visiting.remove(key)
        visited.add(key)
    for key in claims:
        visit(key)
    return sources, claims


CORE = {"product", "sales_territory", "customer", "purchaser", "calendar"}


def blueprint(data, claims):
    obj(data, "blueprint")
    for key in ("slice", "economic_policy", "overlap_policy"):
        text(data.get(key), f"blueprint.{key}")
    texts(data.get("exclusions"), "blueprint.exclusions")
    dims = keyed(data.get("dimensions"), "dimensions")
    require(CORE <= dims.keys(), "blueprint: missing core dimensions")
    for key, dim in dims.items():
        for field in ("grain", "primary_key", "unknown_policy", "history_policy", "generation_rule"):
            text(dim.get(field), f"dimension {key}.{field}")
        attrs = obj(dim.get("attributes"), f"dimension {key}.attributes")
        require(dim["primary_key"] in attrs, f"dimension {key}: primary key not declared")
        require(all(isinstance(k, str) and v in ("string", "integer", "decimal", "date", "boolean")
                    for k, v in attrs.items()), f"dimension {key}: invalid attribute type")
        levels = keyed(dim.get("hierarchy"), f"dimension {key}.hierarchy")
        for lid, level in levels.items():
            text(level.get("key"), f"hierarchy {lid}.key")
            require(level["key"] in attrs, f"hierarchy {lid}: key not declared")
            parent = level.get("parent")
            require(parent is None or isinstance(parent, str) and parent in levels,
                    f"hierarchy {lid}: unknown parent")
            seen, current = set(), lid
            while current is not None:
                require(isinstance(current, str) and current in levels, f"dimension {key}: unknown hierarchy parent")
                require(current not in seen, f"dimension {key}: hierarchy cycle")
                seen.add(current)
                current = levels[current].get("parent")
        provenance = obj(dim.get("provenance"), f"dimension {key}.provenance")
        require(provenance.get("kind") in ("reported", "synthetic"), f"dimension {key}: invalid provenance")
        refs = seq(provenance.get("claim_ids"), f"dimension {key}.claim_ids")
        require(all(isinstance(x, str) and x in claims and claims[x]["status"] != "unknown" for x in refs),
                f"dimension {key}: invalid evidence reference")
        if provenance["kind"] == "reported":
            require(refs and all(claims[x]["status"] == "reported" for x in refs),
                    f"dimension {key}: reported structure needs reported evidence")
        else:
            text(provenance.get("rationale"), f"dimension {key}.rationale")
    relationships = keyed(data.get("relationships"), "relationships")
    purchaser_link = False
    for key, rel in relationships.items():
        child, parent = rel.get("from"), rel.get("to")
        require(isinstance(child, str) and child in dims and isinstance(parent, str) and parent in dims,
                f"relationship {key}: unknown dimension")
        require(rel.get("cardinality") in ("many_to_one", "one_to_one", "many_to_many"),
                f"relationship {key}: invalid cardinality")
        require(isinstance(rel.get("foreign_key"), str) and rel["foreign_key"] in dims[child]["attributes"], f"relationship {key}: missing foreign key")
        for field in ("temporal_rule", "aggregation_rule"):
            text(rel.get(field), f"relationship {key}.{field}")
        if rel["cardinality"] == "many_to_many":
            text(rel.get("bridge"), f"relationship {key}.bridge")
        if child == "purchaser" and parent == "customer":
            purchaser_link = rel["cardinality"] == "many_to_one"
    require(purchaser_link, "blueprint: purchasers must map many-to-one to customers")
    facts = keyed(data.get("facts"), "facts")
    require("order_lines" in facts, "blueprint: order_lines fact required")
    for key, fact in facts.items():
        for field in ("grain", "primary_key", "date_field", "allocation_policy"):
            text(fact.get(field), f"fact {key}.{field}")
        fks = obj(fact.get("dimension_keys"), f"fact {key}.dimension_keys")
        require(all(k in dims and isinstance(v, str) and v for k, v in fks.items()),
                f"fact {key}: invalid dimension keys")
        texts(fact.get("measures"), f"fact {key}.measures")
    require(CORE <= facts["order_lines"]["dimension_keys"].keys(), "order_lines: missing core dimension keys")
    stories = keyed(data.get("stories"), "stories")
    require(2 <= len(stories) <= 3, "blueprint: propose two or three stories")
    for key, story in stories.items():
        require(story.get("status") == "simulated", f"story {key}: must be labeled simulated")
        for field in ("title", "mechanism", "scope", "comparison_basis", "timing", "effect_bounds"):
            text(story.get(field), f"story {key}.{field}")
        for field in ("operational_evidence", "alternatives", "prohibited_claims"):
            texts(story.get(field), f"story {key}.{field}")
        refs = seq(story.get("claim_ids"), f"story {key}.claim_ids")
        require(all(isinstance(x, str) and x in claims and claims[x]["status"] != "unknown" for x in refs),
                f"story {key}: invalid evidence")
        if not refs:
            text(story.get("synthetic_rationale"), f"story {key}.synthetic_rationale")
    return dims


def review(data, claims):
    obj(data, "review")
    decisions = seq(data.get("claim_reviews"), "review.claim_reviews")
    seen = set()
    for item in decisions:
        obj(item, "review item")
        key = item.get("claim_id")
        require(isinstance(key, str) and key in claims and key not in seen, "review: invalid or repeated claim")
        seen.add(key)
        require(item.get("disposition") in ("accepted", "revise", "unresolved"), "review: invalid disposition")
        text(item.get("reason"), "review.reason")
        if claims[key]["status"] == "unknown" or claims[key].get("conflicts_with"):
            require(item["disposition"] != "accepted", "review: unknown or conflicting claim cannot be accepted")
    require(seen == claims.keys(), "review: every claim needs a decision")
    texts(data.get("blockers"), "review.blockers", 0)
    texts(data.get("warnings"), "review.warnings", 0)
    text(data.get("blueprint_assessment"), "review.blueprint_assessment")


def bundle(data):
    obj(data, "bundle")
    require(data.get("schema_version") == 1, "bundle: schema_version must be 1")
    spec = brief(data.get("brief"))
    sources, claims = research(data.get("research"), spec)
    blueprint(data.get("blueprint"), claims)
    review(data.get("review"), claims)
    # A rejected claim cannot silently underpin a proposed hierarchy or story.
    accepted = {r["claim_id"] for r in data["review"]["claim_reviews"] if r["disposition"] == "accepted"}
    for key in accepted:
        if claims[key]["status"] == "inferred":
            require(set(claims[key]["input_claim_ids"]) <= accepted,
                    f"claim {key}: accepted inference depends on unaccepted evidence")
    used = {c for d in data["blueprint"]["dimensions"] for c in d["provenance"]["claim_ids"]}
    used |= {c for s in data["blueprint"]["stories"] for c in s["claim_ids"]}
    require(used <= accepted, "bundle: blueprint depends on unaccepted claims")
    return data
