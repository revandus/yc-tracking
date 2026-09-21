#!/usr/bin/env python3
"""render_report.py - build the weekly Markdown report from report-data + known-status JSON.

Layout (v2, 2026-09-21):
  1. Latest batch spotlight: every qualifying company from the newest tracked batch, new and in-motion alike.
  2. New to Lightspeed: all batches, all tiers in one table (tier is a column), with founders, LinkedIn and contacts.
  3. Already in motion: compact table with who met whom and when.
  4. Per-company entries (contacts, per-founder inclusion reasons), then probe, appendices, run log.

Usage: python3 render_report.py --data state/candidates/report-data-DATE.json --known state/candidates/known-status-DATE.json --date DATE [--latest F26] [--contacts state/candidates/contacts-DATE.json]
"""
import argparse, json, os
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
STATUS_LABEL = {"met": "Met", "in_process": "In process", "contacted": "Contacted", "in_crm": "In Affinity, no contact", "not_in_crm": "New to Lightspeed"}
NEW_STATES = ("not_in_crm", "in_crm")
BATCH_ORDER = {"W": 0, "X": 1, "S": 2, "F": 3}


def batch_key(code):  # later batches sort higher
    return (2000 + int(code[1:]), BATCH_ORDER.get(code[0], 9))


def region_short(rs):
    return ", ".join({"Southeast Asia": "SEA", "Hong Kong": "HK"}.get(r, r) for r in (rs or []))


def desc(r):
    return (r.get("description") or r.get("one_liner") or "").strip().rstrip(".")


def founders_cell(r, contacts):
    out = []
    for f in r.get("founders", []):
        name = f.get("name", "?"); li = f.get("linkedin")
        s = f"[{name}]({li})" if li else name
        title = (f.get("title") or "").strip()
        if title:
            s += f" ({title[:26]})"
        em = (contacts.get(r["key"], {}).get("founder_emails") or {}).get(name)
        if em:
            s += f" · {em}"
        out.append(s)
    return "<br>".join(out) if out else "no founders on record in Harmonic"


def contacts_cell(r, contacts):
    parts = []
    if r.get("domain"):
        parts.append(f"[{r['domain']}](https://{r['domain']})")
    if r.get("yc_url"):
        parts.append(f"[YC]({r['yc_url']})")
    c = contacts.get(r["key"], {})
    for e in (c.get("company_emails") or [])[:2]:
        parts.append(e)
    if c.get("phone"):
        parts.append(c["phone"])
    if r.get("harmonic_id"):
        parts.append(f"[Harmonic](https://console.harmonic.ai/dashboard/company/{r['harmonic_id']})")
    return " · ".join(parts)


def why_cell(r):
    return (r.get("primary_reason") or "")[:140]


def founder_line(f, contacts_for_company):
    rr = f.get("reason") or {}
    crit = rr.get("criterion"); lab = rr.get("label") or "no personal tie stated"; reg = rr.get("region")
    why = (f"**{crit}** · {lab}" + (f" → {reg}" if reg else "")) if crit else "no personal tie stated"
    li = f.get("linkedin"); name = f.get("name", "?"); title = (f.get("title") or "").strip()
    link = f"[LinkedIn]({li})" if li else "no LinkedIn on record"
    em = (contacts_for_company.get("founder_emails") or {}).get(name)
    return f"  - **{name}** ({title}) — {link}" + (f" · {em}" if em else "") + f". Included because: {why}."


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True); ap.add_argument("--known", required=True); ap.add_argument("--date", required=True)
    ap.add_argument("--latest", default=None, help="batch code to spotlight; default = newest batch with qualifying companies")
    ap.add_argument("--contacts", default=None, help="JSON {key: {company_emails:[], phone:'', founder_emails:{name:email}}}")
    a = ap.parse_args()
    data = json.load(open(a.data)); known = {k: v for k, v in json.load(open(a.known)).items() if not k.startswith("_")}
    contacts = json.load(open(a.contacts)) if a.contacts and os.path.exists(a.contacts) else {}
    main_list = data["main"]; appx = data["appendix_likely"]; excl = data["excluded"]; unen = data["unenriched"]; counts = data["counts"]

    def ks(name):
        return known.get(name, {"status": "not_in_crm", "detail": "Not checked", "warm": "not checked"})

    latest = a.latest or max({r["batch"] for r in main_list}, key=batch_key)
    spotlight = sorted([r for r in main_list if r["batch"] == latest], key=lambda r: (0 if ks(r["name"])["status"] in NEW_STATES else 1, 0 if r["tier"] == "confirmed" else 1, r["name"].lower()))
    new = sorted([r for r in main_list if ks(r["name"])["status"] in NEW_STATES], key=lambda r: (0 if r["tier"] == "confirmed" else 1, -batch_key(r["batch"])[0], -batch_key(r["batch"])[1], r["name"].lower()))
    motion = sorted([r for r in main_list if ks(r["name"])["status"] not in NEW_STATES], key=lambda r: (-batch_key(r["batch"])[0], -batch_key(r["batch"])[1], r["name"].lower()))
    tot = sum(c["companies"] for c in counts.values())

    L = []; A = L.append
    A(f"# YC Nexus Scout — {a.date}\n")
    A("Coverage: Southeast Asia · Korea · Australia · Hong Kong · Taiwan · Japan · China  ")
    A(f"Universe: **{tot}** companies evaluated ({', '.join(f'{b} {c[chr(99)+chr(111)+chr(109)+chr(112)+chr(97)+chr(110)+chr(105)+chr(101)+chr(115)]}' for b, c in sorted(counts.items()))}) · **{len(main_list)}** qualify · **{len(new)}** new to Lightspeed · {len(motion)} already in motion · {len(appx)} weak proxies in Appendix A · {len(excl)} excluded\n")
    A("**Why included:** A company based in region · B stated nationality or origin · C founder currently based in region · D formative ties (high school, university, national service) · E worked in region or at a regionally headquartered employer · F market or operations in region. A, B, C = *Confirmed*; D, E, F alone = *Likely* (origin proxy). Nationality is never inferred from names.\n")

    A(f"## 1. Latest batch spotlight — {latest} ({len(spotlight)} qualifying)\n")
    A("| # | Company | What it does | Why included | Region | Tier | Status | Founders (LinkedIn) | Contacts |"); A("|---|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(spotlight, 1):
        k = ks(r["name"])
        A(f"| {i} | **{r['name']}** | {desc(r)[:100]} | {why_cell(r)} | {region_short(r.get('regions'))} | {r['tier'].title()} | {STATUS_LABEL[k['status']]} | {founders_cell(r, contacts)} | {contacts_cell(r, contacts)} |")

    A(f"\n## 2. New to Lightspeed — all batches ({len(new)})\n")
    A("| # | Company | Batch | What it does | Why included | Region | Tier | Founders (LinkedIn) | Contacts | Warm path |"); A("|---|---|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(new, 1):
        k = ks(r["name"])
        A(f"| {i} | **{r['name']}** | {r['batch']} | {desc(r)[:100]} | {why_cell(r)} | {region_short(r.get('regions'))} | {r['tier'].title()} | {founders_cell(r, contacts)} | {contacts_cell(r, contacts)} | {k['warm']} |")

    A(f"\n## 3. Already in motion with Lightspeed ({len(motion)})\n")
    A("| # | Company | Batch | What it does | Why included | Tier | Status (who, when) | Founders (LinkedIn) |"); A("|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(motion, 1):
        k = ks(r["name"])
        A(f"| {i} | **{r['name']}** | {r['batch']} | {desc(r)[:90]} | {why_cell(r)} | {r['tier'].title()} | {STATUS_LABEL[k['status']]}: {k['detail']} | {founders_cell(r, contacts)} |")

    A("\n## 4. Entries\n")
    for r in new + motion:
        k = ks(r["name"]); c = contacts.get(r["key"], {})
        A(f"### {r['name']} — {r['batch']} · {r['tier'].title()} · {region_short(r.get('regions'))}")
        A(f"- **What it does:** {desc(r)}.")
        A(f"- **HQ:** {r.get('hq') or 'not stated'} · **Team size:** {r.get('headcount') or 'n/a'} · **Contacts:** {contacts_cell(r, contacts) or 'none on record'}")
        cr = r.get("company_reason")
        A("- **Included because:**")
        A("  - Company — " + (f"**{cr['criterion']}** · {cr['label']} → {cr.get('region', '')} ({cr.get('source', '')})" if cr else "no company-level tie (HQ outside coverage regions)"))
        for f in r.get("founders", []):
            A(founder_line(f, c))
        if r.get("retier_note"):
            A(f"- **Tier note:** re-tiered to Confirmed — {r['retier_note']}.")
        A(f"- **Status:** {STATUS_LABEL[k['status']]} — {k['detail']}. **Warm path:** {k['warm']}.")
        if r.get("harmonic_lists"):
            A(f"- **Harmonic lists:** {', '.join(r['harmonic_lists'])}.")
        A("")

    A("## Probe: next batches\n" + data.get("probe_note", "- see run log") + "\n")
    A(f"## Appendix A — Weak proxies ({len(appx)}), not recommended for outreach on nexus grounds\n")
    A("| Company | Batch | Region | Basis |"); A("|---|---|---|---|")
    for r in appx:
        A(f"| {r['name']} | {r['batch']} | {region_short(r.get('regions'))} | {(r.get('primary_reason') or '')[:160]} |")
    A(f"\n## Appendix B — Excluded ({len(excl)}): no stated tie to a coverage region\n")
    A(", ".join(sorted(e["name"] for e in excl if e.get("name"))))
    A(f"\n\n## Appendix C — Could not be enriched ({len(unen)})\n")
    for u in unen:
        A(f"- {u.get('name')} ({u.get('batch')}): {u.get('reason')}")
    A("\n## Run log\n" + data.get("run_log", "- (not recorded)") + "\n- Feedback: `python3 scripts/ycscout.py feedback --key <domain> --verdict worth_meeting|maybe|no`\n")

    # Never clobber an existing report for the same date. A same-day rerun (e.g. a
    # validation run of the cloud routine) would otherwise render a delta-only report
    # over the full one and then push that over the good copy.
    rdir = os.path.join(ROOT, "state", "reports"); os.makedirs(rdir, exist_ok=True)
    stem = a.date
    if os.path.exists(os.path.join(rdir, f"{stem}.md")):
        n = 2
        while os.path.exists(os.path.join(rdir, f"{a.date}-rerun{n}.md")):
            n += 1
        stem = f"{a.date}-rerun{n}"
    out = os.path.join(rdir, f"{stem}.md")
    open(out, "w").write("\n".join(L))
    cut = next((i for i, l in enumerate(L) if l.lstrip().startswith("## 4. Entries")), len(L))
    summ = os.path.join(rdir, f"{stem}.summary.md"); open(summ, "w").write("\n".join(L[:cut]))
    print(json.dumps({"report": out, "summary": summ, "latest": latest, "spotlight": len(spotlight), "new": len(new), "in_motion": len(motion), "lines": len(L)}))


if __name__ == "__main__":
    main()
