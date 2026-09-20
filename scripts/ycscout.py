#!/usr/bin/env python3
"""ycscout.py - deterministic helpers for the yc-nexus-scout skill. Standard library only.

Commands (all print JSON to stdout):
  batches [--date YYYY-MM-DD]            batches to track today (forming / in_session / post_demo) plus probes
  snapshot <CODE|slug>                   fetch the public YC directory for a batch, store a dated snapshot, diff vs previous
  harvest <saved-tool-result.txt> --batch CODE
                                         parse a Harmonic company search result (lean fields) into compact JSON
  union --batch CODE                     merge latest Harmonic harvest + YC snapshot for a batch by domain/name
  classify --batch CODE                  compare the union with the registry: new / changed / seen
  geo-scan <text-or-file>                list geo vocabulary hits in arbitrary text (locations, institutions, employers)
  registry-find [--key K] [--batch CODE] [--status S]
  registry-upsert --json '{...}'         upsert one registry record (key = domain or yc slug or harmonic id)
  feedback --key K --verdict worth_meeting|maybe|no [--note ...]
"""
import argparse, datetime as dt, hashlib, json, os, re, sys, urllib.error, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STATE = os.path.join(ROOT, "state")
CONFIG = json.load(open(os.path.join(ROOT, "config.json")))
REGISTRY = os.path.join(STATE, "registry.jsonl")
FEEDBACK = os.path.join(STATE, "feedback.jsonl")
YC_API = "https://yc-oss.github.io/api/batches/{slug}.json"
SEASON_ORDER = ["W", "X", "S", "F"]


def geo_terms():
    """Flatten config geo regions into (term, category, region) tuples, longest terms first."""
    rows = []
    for region, cats in CONFIG["geo"]["regions"].items():
        for cat, terms in cats.items():
            for t in terms:
                rows.append((t, cat, region))
    rows.sort(key=lambda r: -len(r[0]))
    return rows


GEO = geo_terms()


def geo_hits(text, cats=None):
    """Vocabulary hits in text, each tagged with category and region. Word-bounded, case-insensitive."""
    low = (text or "").lower()
    hits = []
    for term, cat, region in GEO:
        if cats and cat not in cats:
            continue
        if re.search(r"(?<![a-z])" + re.escape(term.lower()) + r"(?![a-z])", low):
            hits.append({"term": term, "category": cat, "region": region})
    return hits


def out(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def die(msg):
    sys.stderr.write("error: %s\n" % msg)
    sys.exit(1)


def today(s=None):
    return dt.date.fromisoformat(s) if s else dt.date.today()


# ---------------- batch calendar ----------------
def batch_dates(code):
    """code like 'F26' -> dict with start, demo, forming_from, tracked_until (dates)."""
    letter, yy = code[0], int(code[1:])
    year = 2000 + yy
    d = CONFIG["batches"]["defaults"][letter]
    ov = CONFIG["batches"]["overrides"].get(code, {})
    start = dt.date.fromisoformat(ov["start"]) if "start" in ov else dt.date.fromisoformat("%d-%s" % (year, d["start"]))
    demo = dt.date.fromisoformat(ov["demo"]) if "demo" in ov else dt.date.fromisoformat("%d-%s" % (year, d["demo"]))
    lead = int(ov.get("forming_lead_days", CONFIG["batches"]["forming_lead_days"]))
    post = int(ov.get("post_demo_days", CONFIG["batches"]["post_demo_days"]))
    return {
        "code": code, "letter": letter, "year": year, "season": d["season"],
        "slug": "%s-%d" % (d["slug_season"], year),
        "harmonic_label": "Y Combinator - %s" % code,
        "harmonic_query": CONFIG["harmonic"]["cohort_query"].format(season=d["season"], year=year, code=code),
        "start": start, "demo": demo,
        "forming_from": start - dt.timedelta(days=lead),
        "tracked_until": demo + dt.timedelta(days=post),
    }


def all_codes(center_year):
    return ["%s%02d" % (l, y % 100) for y in range(center_year - 1, center_year + 2) for l in SEASON_ORDER]


def phase_for(b, day):
    if day < b["forming_from"]:
        return "future"
    if day < b["start"]:
        return "forming"
    if day <= b["demo"]:
        return "in_session"
    if day <= b["tracked_until"]:
        return "post_demo"
    return "archived"


def cmd_batches(args):
    day = today(args.date)
    rows = []
    for code in all_codes(day.year):
        b = batch_dates(code)
        b["phase"] = phase_for(b, day)
        rows.append(b)
    tracked = [b for b in rows if b["phase"] in ("forming", "in_session", "post_demo")]
    future = [b for b in rows if b["phase"] == "future"]
    probes = future[: int(CONFIG["batches"]["probe_ahead"])]

    def ser(b):
        return {k: (v.isoformat() if isinstance(v, dt.date) else v) for k, v in b.items()}

    out({"date": day.isoformat(), "tracked": [ser(b) for b in tracked], "probe": [ser(b) for b in probes],
         "note": "Probe batches: run the Harmonic cohort query anyway; if Harmonic already returns companies, treat the batch as forming."})


def resolve_code(s):
    s = s.strip()
    if re.fullmatch(r"[WXSF]\d{2}", s.upper()):
        return s.upper()
    m = re.fullmatch(r"(winter|spring|summer|fall)-(\d{4})", s.lower())
    if not m:
        die("batch must be a code like F26 or a slug like fall-2026")
    letter = {"winter": "W", "spring": "X", "summer": "S", "fall": "F"}[m.group(1)]
    return "%s%02d" % (letter, int(m.group(2)) % 100)


# ---------------- helpers ----------------
def norm_domain(url):
    if not url:
        return None
    u = url.strip().lower()
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    return u.split("/")[0].split("?")[0] or None


def norm_name(name):
    n = (name or "").lower()
    n = re.sub(r"\(yc [wxsf]\d{2}\)", "", n)
    n = re.sub(r"\b(inc|labs?|ai|technologies|technology|co|corp|ltd|pte|llc)\b", "", n)
    return re.sub(r"[^a-z0-9]", "", n)


def fingerprint(rec):
    keys = ["name", "domain", "hq", "one_liner", "team_size", "founders", "status", "harmonic_id", "yc_slug"]
    payload = json.dumps({k: rec.get(k) for k in keys}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]


def latest_file(folder, suffix=".json", exclude=None):
    if not os.path.isdir(folder):
        return None
    files = sorted(f for f in os.listdir(folder) if f.endswith(suffix) and f != exclude)
    return os.path.join(folder, files[-1]) if files else None


# ---------------- YC public directory ----------------
def cmd_snapshot(args):
    code = resolve_code(args.batch)
    b = batch_dates(code)
    url = YC_API.format(slug=b["slug"])
    note = None
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            data, note = [], "YC directory has no page for %s yet (404); treating as empty" % b["slug"]
        else:
            die("fetch failed for %s: HTTP %s" % (url, e.code))
    except Exception as e:  # noqa
        die("fetch failed for %s: %s" % (url, e))
    rows = []
    for c in data:
        loc = c.get("all_locations") or ""
        rows.append({
            "yc_id": c.get("id"), "name": c.get("name"), "yc_slug": c.get("slug"),
            "website": c.get("website"), "domain": norm_domain(c.get("website")),
            "hq": loc, "one_liner": c.get("one_liner"), "team_size": c.get("team_size"),
            "industry": c.get("industry"), "tags": c.get("tags") or [], "status": c.get("status"),
            "launched_at": dt.datetime.fromtimestamp(c["launched_at"], dt.timezone.utc).date().isoformat() if c.get("launched_at") else None,
            "yc_url": c.get("url"), "long_description": (c.get("long_description") or "")[:600],
            "hq_geo_hit": geo_hits(loc, cats=("countries", "cities")),
        })
    folder = os.path.join(STATE, "snapshots", b["slug"])
    os.makedirs(folder, exist_ok=True)
    fname = today().isoformat() + ".json"
    prev_path = latest_file(folder, exclude=fname)
    path = os.path.join(folder, fname)
    json.dump(rows, open(path, "w"), indent=1, ensure_ascii=False)
    prev = json.load(open(prev_path)) if prev_path else []
    by_id_prev = {r["yc_id"]: r for r in prev}
    by_id_now = {r["yc_id"]: r for r in rows}
    added = [r for r in rows if r["yc_id"] not in by_id_prev]
    removed = [r for r in prev if r["yc_id"] not in by_id_now]
    changed = []
    for i, r in by_id_now.items():
        p = by_id_prev.get(i)
        if not p:
            continue
        diffs = {k: [p.get(k), r.get(k)] for k in ("name", "website", "hq", "one_liner", "team_size", "status", "tags") if p.get(k) != r.get(k)}
        if diffs:
            changed.append({"yc_id": i, "name": r["name"], "changes": diffs})
    out({"batch": code, "slug": b["slug"], "note": note, "snapshot": path, "previous": prev_path if prev else None,
         "total": len(rows), "added": added, "removed": [{"yc_id": r["yc_id"], "name": r["name"]} for r in removed],
         "changed": changed, "hq_geo_hits": [{"name": r["name"], "hq": r["hq"], "regions": sorted({h["region"] for h in r["hq_geo_hit"]})} for r in rows if r["hq_geo_hit"]]})


# ---------------- Harmonic saved-result harvest ----------------
def cmd_harvest(args):
    code = resolve_code(args.batch)
    text = open(args.file, encoding="utf-8", errors="replace").read()
    if "investor_accelerator_filter" not in text or ("Y Combinator - %s" % code) not in text:
        sys.stderr.write("warning: result does not show an accelerator filter for %s; Harmonic may not have this cohort yet\n" % code)
    blocks = re.split(r"\n  - name: ", "\n" + text)[1:]
    rows = []
    for blk in blocks:
        name = blk.split("\n", 1)[0].strip().strip('"')
        def grab(pat):
            m = re.search(pat, blk, re.M)
            return m.group(1).strip().strip('"') if m else None
        hid = grab(r"^    id: (\d+)")
        rows.append({
            "harmonic_id": int(hid) if hid else None,
            "name": name, "name_clean": re.sub(r"\s*\(YC [WXSF]\d{2}\)\s*$", "", name),
            "domain": norm_domain(grab(r"^      domain: (.+)$") or grab(r"^        domain: (.+)$")),
            "website": grab(r"^      url: (.+)$") or grab(r"^        url: (.+)$"),
            "hq_country": grab(r"^      country: (.+)$") or grab(r"^        country: (.+)$"),
            "hq_city": grab(r"^      city: (.+)$") or grab(r"^        city: (.+)$"),
            "headcount": grab(r"^    headcount: (\d+)"),
            "description": (grab(r"^    description: (.+)$") or "")[:600],
        })
    m = re.search(r"^count: (\d+)", text, re.M)
    folder = os.path.join(STATE, "harvest", code)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, today().isoformat() + ".json")
    existing = json.load(open(path)) if os.path.exists(path) else []
    by_id = {r["harmonic_id"]: r for r in existing if r.get("harmonic_id")}
    for r in rows:
        if r.get("harmonic_id"):
            old = by_id.get(r["harmonic_id"], {})
            by_id[r["harmonic_id"]] = {k: (v if v is not None else old.get(k)) for k, v in r.items()}
    merged = list(by_id.values()) + [r for r in existing + rows if not r.get("harmonic_id")]
    json.dump(merged, open(path, "w"), indent=1, ensure_ascii=False)
    out({"batch": code, "parsed_this_file": len(rows), "reported_count": int(m.group(1)) if m else None,
         "harvest_file": path, "harvest_total": len(merged),
         "has_next": bool(re.search(r"^  has_next: true", text, re.M))})


# ---------------- union + classify ----------------
def load_union_inputs(code):
    b = batch_dates(code)
    hv = latest_file(os.path.join(STATE, "harvest", code))
    sn = latest_file(os.path.join(STATE, "snapshots", b["slug"]))
    return (json.load(open(hv)) if hv else []), (json.load(open(sn)) if sn else []), hv, sn


def cmd_union(args):
    code = resolve_code(args.batch)
    harm, yc, hv, sn = load_union_inputs(code)
    by_key = {}
    for r in harm:
        key = r.get("domain") or ("harmonic:%s" % r.get("harmonic_id"))
        by_key[key] = {"key": key, "batch": code, "name": r["name_clean"], "domain": r.get("domain"), "website": r.get("website"),
                       "hq": ", ".join(x for x in [r.get("hq_city"), r.get("hq_country")] if x), "harmonic_id": r.get("harmonic_id"),
                       "headcount": r.get("headcount"), "one_liner": r.get("description"), "sources": ["harmonic"]}
    name_index = {norm_name(v["name"]): k for k, v in by_key.items()}
    for r in yc:
        key = r.get("domain") or name_index.get(norm_name(r["name"])) or ("yc:%s" % r["yc_slug"])
        if key not in by_key and norm_name(r["name"]) in name_index:
            key = name_index[norm_name(r["name"])]
        rec = by_key.setdefault(key, {"key": key, "batch": code, "name": r["name"], "sources": []})
        rec.update({k: v for k, v in {"domain": rec.get("domain") or r.get("domain"), "website": rec.get("website") or r.get("website"),
                                       "hq": rec.get("hq") or r.get("hq"), "yc_slug": r["yc_slug"], "yc_url": r.get("yc_url"),
                                       "one_liner": r.get("one_liner") or rec.get("one_liner"), "team_size": r.get("team_size"),
                                       "tags": r.get("tags"), "status": r.get("status"), "launched_at": r.get("launched_at"),
                                       "hq_geo_hit": r.get("hq_geo_hit")}.items() if v is not None})
        if "yc_directory" not in rec["sources"]:
            rec["sources"].append("yc_directory")
    rows = list(by_key.values())
    folder = os.path.join(STATE, "candidates", code)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, today().isoformat() + ".union.json")
    json.dump(rows, open(path, "w"), indent=1, ensure_ascii=False)
    out({"batch": code, "harvest_file": hv, "snapshot_file": sn, "union_file": path, "total": len(rows),
         "harmonic_only": sum(1 for r in rows if r["sources"] == ["harmonic"]),
         "yc_only": sum(1 for r in rows if r["sources"] == ["yc_directory"]),
         "both": sum(1 for r in rows if len(r["sources"]) == 2)})


def read_registry():
    if not os.path.exists(REGISTRY):
        return {}
    recs = {}
    for line in open(REGISTRY, encoding="utf-8"):
        line = line.strip()
        if line:
            r = json.loads(line)
            recs[r["key"]] = r  # last write wins
    return recs


def cmd_classify(args):
    code = resolve_code(args.batch)
    path = latest_file(os.path.join(STATE, "candidates", code), ".union.json")
    if not path:
        die("run union first")
    rows = json.load(open(path))
    reg = read_registry()
    res = {"new": [], "changed": [], "seen": [], "suppressed": []}
    for r in rows:
        prev = reg.get(r["key"]) or (reg.get(r["domain"]) if r.get("domain") else None)
        fp = fingerprint(r)
        if not prev:
            res["new"].append({**r, "fingerprint": fp})
        elif prev.get("verdict") == "no" and prev.get("fingerprint") == fp:
            res["suppressed"].append({"key": r["key"], "name": r["name"], "reason": "marked no, unchanged"})
        elif prev.get("fingerprint") != fp:
            res["changed"].append({**r, "fingerprint": fp, "previous_fingerprint": prev.get("fingerprint"), "previous_seen": prev.get("last_seen")})
        else:
            res["seen"].append({"key": r["key"], "name": r["name"], "last_seen": prev.get("last_seen"), "nexus_tier": prev.get("nexus_tier")})
    outpath = path.replace(".union.json", ".classified.json")
    json.dump(res, open(outpath, "w"), indent=1, ensure_ascii=False)
    out({"batch": code, "classified_file": outpath, "counts": {k: len(v) for k, v in res.items()},
         "to_enrich": [{"key": r["key"], "name": r["name"], "harmonic_id": r.get("harmonic_id"), "domain": r.get("domain")} for r in res["new"] + res["changed"]]})


# ---------------- geo scan ----------------
def cmd_geo_scan(args):
    text = open(args.text).read() if os.path.exists(args.text) else args.text
    by_region = {}
    for h in geo_hits(text):
        bucket = by_region.setdefault(h["region"], {}).setdefault(h["category"], [])
        if h["term"] not in bucket:
            bucket.append(h["term"])
    out(by_region)


# ---------------- registry ----------------
def cmd_registry_find(args):
    reg = read_registry()
    rows = [r for r in reg.values() if (not args.key or r["key"] == args.key or r.get("domain") == args.key)
            and (not args.batch or r.get("batch") == resolve_code(args.batch)) and (not args.status or r.get("status") == args.status)]
    out({"count": len(rows), "records": rows})


def cmd_registry_upsert(args):
    rec = json.loads(args.json)
    if "key" not in rec:
        die("record needs a key (domain, yc:<slug>, or harmonic:<id>)")
    reg = read_registry()
    prev = reg.get(rec["key"], {})
    now = dt.datetime.now().isoformat(timespec="seconds")
    merged = {**prev, **rec, "first_seen": prev.get("first_seen", rec.get("first_seen", now)), "last_seen": now}
    merged.setdefault("fingerprint", fingerprint(merged))
    os.makedirs(STATE, exist_ok=True)
    with open(REGISTRY, "a", encoding="utf-8") as f:
        f.write(json.dumps(merged, ensure_ascii=False) + "\n")
    out({"upserted": merged})


def cmd_feedback(args):
    reg = read_registry()
    if args.key not in reg:
        die("unknown key %s" % args.key)
    now = dt.datetime.now().isoformat(timespec="seconds")
    with open(FEEDBACK, "a", encoding="utf-8") as f:
        f.write(json.dumps({"at": now, "key": args.key, "verdict": args.verdict, "note": args.note}, ensure_ascii=False) + "\n")
    rec = {**reg[args.key], "verdict": args.verdict, "verdict_at": now, "verdict_note": args.note, "last_seen": now}
    with open(REGISTRY, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    out({"recorded": rec})


# ---------------- main ----------------
def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("batches"); s.add_argument("--date"); s.set_defaults(fn=cmd_batches)
    s = sub.add_parser("snapshot"); s.add_argument("batch"); s.set_defaults(fn=cmd_snapshot)
    s = sub.add_parser("harvest"); s.add_argument("file"); s.add_argument("--batch", required=True); s.set_defaults(fn=cmd_harvest)
    s = sub.add_parser("union"); s.add_argument("--batch", required=True); s.set_defaults(fn=cmd_union)
    s = sub.add_parser("classify"); s.add_argument("--batch", required=True); s.set_defaults(fn=cmd_classify)
    s = sub.add_parser("geo-scan"); s.add_argument("text"); s.set_defaults(fn=cmd_geo_scan)
    s = sub.add_parser("registry-find"); s.add_argument("--key"); s.add_argument("--batch"); s.add_argument("--status"); s.set_defaults(fn=cmd_registry_find)
    s = sub.add_parser("registry-upsert"); s.add_argument("--json", required=True); s.set_defaults(fn=cmd_registry_upsert)
    s = sub.add_parser("feedback"); s.add_argument("--key", required=True); s.add_argument("--verdict", required=True, choices=["worth_meeting", "maybe", "no"]); s.add_argument("--note", default=""); s.set_defaults(fn=cmd_feedback)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
