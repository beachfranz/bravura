"""Escaped, self-contained authoring review packet and immutable approval snapshot."""
import html
import json
from pathlib import Path
from . import contracts as c


def dump(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def render(data):
    c.bundle(data)
    esc = lambda value: html.escape(str(value), quote=True)
    spec, bp, review = data["brief"], data["blueprint"], data["review"]
    def bullets(items):
        return "<ul>" + "".join(f"<li>{esc(x)}</li>" for x in items) + "</ul>"
    rows = "".join(
        f"<tr><td>{esc(d['id'])}</td><td>{esc(d['grain'])}</td><td>{esc(d['primary_key'])}</td>"
        f"<td>{esc(', '.join(x['id'] for x in d['hierarchy']) or 'Classification / entity')}</td>"
        f"<td>{esc(d['provenance']['kind'])}</td></tr>" for d in bp["dimensions"])
    decisions = {x["claim_id"]: x for x in review["claim_reviews"]}
    claims = "".join(f"<li><strong>{esc(x['id'])} · {esc(x['status'])}</strong>: {esc(x['statement'])} "
                     f"<em>({esc(decisions[x['id']]['disposition'])})</em></li>" for x in data["research"]["claims"])
    stories = "".join(
        f"<article><h3>{esc(s['title'])} <small>SIMULATED</small></h3><p>{esc(s['mechanism'])}</p>"
        f"<p><b>Scope:</b> {esc(s['scope'])}<br><b>Comparison:</b> {esc(s['comparison_basis'])}<br>"
        f"<b>Timing:</b> {esc(s['timing'])}<br><b>Proposed bounds:</b> {esc(s['effect_bounds'])}</p>"
        f"<b>Alternatives</b>{bullets(s['alternatives'])}<b>Do not conclude</b>{bullets(s['prohibited_claims'])}</article>"
        for s in bp["stories"])
    sources = "".join(f"<li><a href='{esc(s['url'])}' rel='noreferrer'>{esc(s['title'])}</a> — "
                      f"published {esc(s['published_date'])}; accessed {esc(s['accessed_date'])}</li>"
                      for s in data["research"]["sources"])
    return f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Bravura · {esc(spec['target'])}</title><style>
body{{font:16px/1.55 system-ui,sans-serif;color:#16312d;background:#f4f6f2;margin:0}}main{{max-width:1080px;margin:40px auto;padding:32px;background:white;border-radius:16px}}
h1{{font-size:36px}}h2{{margin-top:32px}}small,em{{color:#536b65}}.notice{{padding:16px;background:#fff3d6;border-left:4px solid #bd891d}}.stats{{display:flex;gap:28px;flex-wrap:wrap}}article{{padding:18px;background:#f4f6f2;margin:12px 0}}table{{border-collapse:collapse;width:100%;font-size:14px}}td,th{{text-align:left;padding:10px;border-bottom:1px solid #dbe3dd}}a{{color:#126c5a}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}}.scroll{{overflow-x:auto}}@media print{{body{{background:white}}main{{margin:0;padding:0}}details{{display:none}}}}
</style><main><small>BRAVURA / AUTHORING REVIEW / AWAITING USER DECISION</small>
<h1>{esc(spec['target'])}</h1><p>{esc(spec['purpose'])}</p>
<div class="notice">Proposed demo, not actual company transactions. No dataset has been generated. This packet contains intended stories and must not be supplied to a blind analyst.</div>
<div class="stats"><p><b>Audience</b><br>{esc(spec['audience'])}</p><p><b>Proposed order lines</b><br>{spec['order_lines']:,}</p><p><b>Period</b><br>{esc(spec['start_date'])}–{esc(spec['end_date'])}</p><p><b>Cutoff</b><br>{esc(spec['reporting_cutoff'])}</p></div>
<h2>Recognizable slice</h2><p>{esc(bp['slice'])}</p><b>Excluded</b>{bullets(bp['exclusions'])}
<h2>Evidence and gaps</h2><ul>{claims}</ul><p>Structural validation checks references and excerpts; it does not authenticate websites or establish that a claim follows from its source.</p>
<h2>Dimension blueprint</h2><div class="scroll"><table><tr><th>Dimension</th><th>Grain</th><th>Key</th><th>Levels</th><th>Basis</th></tr>{rows}</table></div>
<h2>Proposed stories</h2>{stories}<p><b>Overlap:</b> {esc(bp['overlap_policy'])}</p>
<h2>Economic policy</h2><p>{esc(bp['economic_policy'])}</p>
<h2>Review decisions</h2><p>{esc(review['blueprint_assessment'])}</p><b>Blockers</b>{bullets(review['blockers'])}<b>Warnings</b>{bullets(review['warnings'])}
<p>Review the slice, dimension relationships, simulated stories and assumptions together. Approval freezes this exact bundle; edits require a new approval.</p>
<h2>Sources</h2><ul>{sources}</ul><details><summary>Full contracts and supporting detail</summary><pre>{esc(json.dumps(data, indent=2, ensure_ascii=False))}</pre></details>
<p><small>Bundle SHA-256: {c.digest(data)}</small></p></main></html>"""


def write_packet(data, out):
    c.bundle(data)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for name in ("bundle.json", "review.html", "manifest.json"):
        c.require(not (out / name).exists(), f"refusing to overwrite {name}")
    dump(out / "bundle.json", data)
    (out / "review.html").write_text(render(data))
    dump(out / "manifest.json", {"schema_version": 1, "bundle_sha256": c.digest(data),
         "source_snapshot_sha256": {s["id"]: c.digest(s["snapshot_text"]) for s in data["research"]["sources"]},
         "status": "awaiting_user_review", "generation": "not_run", "blind_evaluation": "not_run"})


def approve(data, reviewer, note, destination):
    c.bundle(data)
    c.text(reviewer, "reviewer")
    c.text(note, "approval note")
    c.require(not data["review"]["blockers"], "cannot approve: unresolved blockers")
    c.require(not any(x["disposition"] == "revise" for x in data["review"]["claim_reviews"]),
              "cannot approve: claims require revision")
    record = {"schema_version": 1, "bundle_sha256": c.digest(data), "reviewer": reviewer,
              "note": note, "bundle": data, "status": "approved_design_only",
              "identity_assurance": "local user declaration; not authenticated signing"}
    with Path(destination).open("x") as stream:
        json.dump(record, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    return record


def verify_approval(record, data):
    c.bundle(data)
    c.require(record.get("status") == "approved_design_only", "not a design approval")
    c.require(record.get("bundle_sha256") == c.digest(data) == c.digest(record.get("bundle")),
              "approval does not match current bundle")
