#!/usr/bin/env python3
"""render_report.py - build the weekly Markdown report from report-data + known-status JSON.
Usage: python3 render_report.py --data state/candidates/report-data-DATE.json --known state/candidates/known-status-DATE.json --date DATE
Writes state/reports/DATE.md and state/reports/DATE.summary.md; prints the paths.
"""
import argparse, json, os
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
CRIT={"A":"A · company based in region","B":"B · stated nationality/origin","C":"C · founder currently based in region","D":"D · formative ties (school / national service)","E":"E · worked in region or at regional employer","F":"F · market or operations in region"}
STATUS_LABEL={"met":"Met","in_process":"In process","contacted":"Contacted","in_crm":"In Affinity, no contact","not_in_crm":"New to Lightspeed"}
ACTION={"met":"Already in motion","in_process":"Already in motion","contacted":"Follow up","in_crm":"Reach out","not_in_crm":"Reach out"}

def region_short(rs): return ", ".join({"Southeast Asia":"SEA","Hong Kong":"HK"}.get(r,r) for r in (rs or []))
def founder_line(f):
    r=f.get("reason") or {}
    crit=r.get("criterion"); lab=r.get("label") or "no personal tie stated"; reg=r.get("region")
    why=(f"**{crit}** · {lab}" + (f" → {reg}" if reg else "")) if crit else "no personal tie stated"
    li=f.get("linkedin"); name=f.get("name","?"); title=(f.get("title") or "").strip()
    link=f"[LinkedIn]({li})" if li else "no LinkedIn on record"
    return f"  - **{name}** ({title}) — {link}. Included because: {why}."
def desc(r): return (r.get("description") or r.get("one_liner") or "").strip().rstrip(".")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data",required=True); ap.add_argument("--known",required=True); ap.add_argument("--date",required=True); a=ap.parse_args()
    data=json.load(open(a.data)); known={k:v for k,v in json.load(open(a.known)).items() if not k.startswith("_")}
    main=data["main"]; appx=data["appendix_likely"]; excl=data["excluded"]; unen=data["unenriched"]; counts=data["counts"]
    def ks(name): return known.get(name,{"status":"not_in_crm","detail":"Not checked","warm":"not checked"})
    new=[r for r in main if ks(r["name"])["status"] in ("not_in_crm","in_crm")]
    motion=[r for r in main if ks(r["name"])["status"] in ("met","in_process","contacted")]
    L=[]; A=L.append
    A(f"# YC Nexus Scout — first run, {a.date}\n")
    A("Batches tracked: **S26** (post demo day 2026-09-10) · **F26** (forming, starts 2026-10-01, demo day 2026-12-02) · **W27** (probe: 1 company already self-declared in Harmonic)  ")
    A("Coverage: Southeast Asia · Korea · Australia · Hong Kong · Taiwan · Japan · China  ")
    tot=sum(c["companies"] for c in counts.values())
    A(f"Universe: **{tot}** companies evaluated ({', '.join(f'{b} {c[chr(99)+chr(111)+chr(109)+chr(112)+chr(97)+chr(110)+chr(105)+chr(101)+chr(115)]}' for b,c in counts.items())}) · **{len(main)}** qualify for the main list ({sum(1 for r in main if r['tier']=='confirmed')} confirmed, {sum(1 for r in main if r['tier']=='likely')} likely) · {len(appx)} weak proxies in Appendix A · {len(excl)} excluded · {len(unen)} could not be enriched\n")
    A("**How to read \"Why included\":** A company based in a coverage region · B founder's stated nationality or origin · C founder currently based in region · D formative ties (high school, university, national service) · E worked in region or at a regionally headquartered employer · F market or operations in region. A, B and C are *Confirmed*; D, E and F alone are *Likely* (origin proxies). Nationality is never inferred from names.\n")
    A(f"## 1. New to Lightspeed — {len(new)} companies to consider meeting\n")
    A("| # | Company | Batch | What it does | Why included | Region | Tier | Status | Warm path |"); A("|---|---|---|---|---|---|---|---|---|")
    for i,r in enumerate(new,1):
        k=ks(r["name"]); A(f"| {i} | **{r['name']}** | {r['batch']} | {desc(r)[:110]} | {(r.get('primary_reason') or '')[:120]} | {region_short(r.get('regions'))} | {r['tier'].title()} | {STATUS_LABEL[k['status']]} | {k['warm']} |")
    A(f"\n## 2. Already in motion with Lightspeed — {len(motion)} companies\n")
    A("| # | Company | Batch | What it does | Why included | Region | Tier | Status (who, when) |"); A("|---|---|---|---|---|---|---|---|")
    for i,r in enumerate(motion,1):
        k=ks(r["name"]); A(f"| {i} | **{r['name']}** | {r['batch']} | {desc(r)[:110]} | {(r.get('primary_reason') or '')[:120]} | {region_short(r.get('regions'))} | {r['tier'].title()} | {STATUS_LABEL[k['status']]}: {k['detail']} |")
    A("\n## 3. Entries\n")
    for section,rows in (("New to Lightspeed",new),("Already in motion",motion)):
        A(f"### {section}\n")
        for r in rows:
            k=ks(r["name"]); A(f"#### {r['name']} — {r['batch']} · {r['tier'].title()} · {region_short(r.get('regions'))}")
            A(f"- **What it does:** {desc(r)}.")
            A(f"- **HQ:** {r.get('hq') or 'not stated'} · **Team size:** {r.get('headcount') or 'n/a'} · **Links:** " + " · ".join(x for x in [f"[website](https://{r['domain']})" if r.get('domain') else None, f"[YC]({r['yc_url']})" if r.get('yc_url') else None, f"[Harmonic](https://console.harmonic.ai/dashboard/company/{r['harmonic_id']})" if r.get('harmonic_id') else None] if x))
            cr=r.get("company_reason")
            A("- **Included because:**"); A(f"  - Company — " + (f"**{cr['criterion']}** · {cr['label']} → {cr.get('region','')} ({cr.get('source','')})" if cr else "no company-level tie (HQ outside coverage regions)"))
            for f in r.get("founders",[]): A(founder_line(f))
            if r.get("retier_note"): A(f"- **Tier note:** re-tiered to Confirmed — {r['retier_note']}.")
            A(f"- **Status:** {STATUS_LABEL[k['status']]} — {k['detail']}. **Warm path:** {k['warm']}. **Suggested action:** {ACTION[k['status']]}.")
            if r.get("harmonic_lists"): A(f"- **Harmonic lists:** {', '.join(r['harmonic_lists'])}.")
            A("")
    A("## Probe: next batches\n- **W27:** Harmonic already tags 1 company (Rote, Ithaca NY, claims-recovery AI for auto body shops) — no regional tie, no founder data. The YC directory also lists it. Tracking starts automatically when W27 enters its forming window.\n- **X27:** Harmonic has no Spring 2027 cohort yet.\n")
    A(f"## Appendix A — Weak proxies ({len(appx)}), kept for transparency, not recommended for outreach on nexus grounds\n")
    A("| Company | Batch | Region | Basis |"); A("|---|---|---|---|")
    for r in appx: A(f"| {r['name']} | {r['batch']} | {region_short(r.get('regions'))} | {(r.get('primary_reason') or '')[:160]} |")
    A(f"\n## Appendix B — Excluded ({len(excl)}): no stated tie to a coverage region\n")
    A(", ".join(sorted(e['name'] for e in excl if e.get('name'))))
    A(f"\n\n## Appendix C — Could not be enriched ({len(unen)})\n")
    for u in unen: A(f"- {u.get('name')} ({u.get('batch')}): {u.get('reason')}")
    A("\n## Run log\n- Harmonic cohort queries: S26 → 266 companies (cohort urn:harmonic:accelerator_cohort:78, 3 pages); F26 → 127 (cohort 479, 2 pages); W27 → 1 (cohort 319); X27 → not in Harmonic.\n- YC directory snapshots: summer-2026 232, fall-2026 79, winter-2027 1 (baseline stored 2026-09-20/21).\n- Enrichment: 15 chunks across 15 subagents, get_companies in pages of 6; 4 companies lacked founder data in Harmonic.\n- Known status: Affinity domain lookups plus relationship intelligence for every main-list company; Harmonic team-network connections for all 62.\n- Feedback: `python3 ~/.claude/skills/yc-nexus-scout/scripts/ycscout.py feedback --key <domain> --verdict worth_meeting|maybe|no`\n")
    out=os.path.join(ROOT,"state","reports",f"{a.date}.md"); os.makedirs(os.path.dirname(out),exist_ok=True); open(out,"w").write("\n".join(L))
    summ=os.path.join(ROOT,"state","reports",f"{a.date}.summary.md"); cut=L.index("## 3. Entries\n") if "## 3. Entries\n" in L else len(L); open(summ,"w").write("\n".join(L[:cut]))
    print(json.dumps({"report":out,"summary":summ,"new":len(new),"in_motion":len(motion),"lines":len(L)}))
if __name__=="__main__": main()
