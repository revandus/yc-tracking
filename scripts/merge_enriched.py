#!/usr/bin/env python3
"""merge_enriched.py - merge per-chunk enrichment files into one dataset for the report.

Usage: python3 merge_enriched.py [--batches S26,F26,W27] [--out state/candidates/merged-YYYY-MM-DD.json]
Prints a summary and writes the merged JSON with: included (sorted confirmed > likely, then by batch),
excluded (one line each), unenriched, and per-batch counts.
"""
import argparse, datetime as dt, glob, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STATE = os.path.join(ROOT, "state")
TIER_ORDER = {"confirmed": 0, "likely": 1}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--batches", default=None, help="comma-separated batch codes; default = every batch with enriched files")
    p.add_argument("--out", default=None)
    a = p.parse_args()
    batches = a.batches.split(",") if a.batches else sorted(
        os.path.basename(os.path.dirname(f)) for f in glob.glob(os.path.join(STATE, "candidates", "*", "enriched-*.json")))
    batches = sorted(set(batches))
    included, excluded, unenriched, counts, chunks_seen = [], [], [], {}, {}
    for b in batches:
        files = sorted(glob.glob(os.path.join(STATE, "candidates", b, "enriched-*.json")))
        chunks_seen[b] = [os.path.basename(f) for f in files]
        c = counts.setdefault(b, {"chunks": len(files), "companies": 0, "confirmed": 0, "likely": 0, "excluded": 0, "unenriched": 0})
        for f in files:
            try:
                d = json.load(open(f))
            except Exception as e:  # noqa
                unenriched.append({"batch": b, "key": os.path.basename(f), "name": "(chunk file unreadable)", "reason": str(e)})
                continue
            for u in d.get("unenriched", []) or []:
                unenriched.append({"batch": b, **u}); c["unenriched"] += 1
            for r in d.get("companies", []) or []:
                r.setdefault("batch", b); c["companies"] += 1
                if r.get("included"):
                    tier = (r.get("tier") or "likely").lower(); r["tier"] = tier
                    c[tier if tier in c else "likely"] += 1
                    included.append(r)
                else:
                    c["excluded"] += 1
                    excluded.append({"batch": b, "name": r.get("name"), "key": r.get("key"), "hq": r.get("hq"),
                                     "founder_locations": [f.get("current_location") for f in r.get("founders", []) if f.get("current_location")],
                                     "note": (r.get("company_reason") or {}).get("label") or "no regional tie stated"})
    # de-duplicate by key (a company can appear in two batches' data only by error)
    seen, uniq = set(), []
    for r in included:
        k = (r.get("key"), r.get("batch"))
        if k in seen:
            continue
        seen.add(k); uniq.append(r)
    uniq.sort(key=lambda r: (TIER_ORDER.get(r.get("tier"), 9), r.get("batch"), (r.get("name") or "").lower()))
    out = a.out or os.path.join(STATE, "candidates", "merged-%s.json" % dt.date.today().isoformat())
    json.dump({"generated_at": dt.datetime.now().isoformat(timespec="seconds"), "batches": batches, "counts": counts,
               "chunks_seen": chunks_seen, "included": uniq, "excluded": excluded, "unenriched": unenriched},
              open(out, "w"), indent=1, ensure_ascii=False)
    print(json.dumps({"out": out, "counts": counts, "included_total": len(uniq),
                      "confirmed": sum(1 for r in uniq if r["tier"] == "confirmed"),
                      "likely": sum(1 for r in uniq if r["tier"] == "likely"),
                      "regions": sorted({x for r in uniq for x in (r.get("regions") or [])})}, indent=2))


if __name__ == "__main__":
    main()
