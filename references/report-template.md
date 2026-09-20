# YC Nexus Scout — week of {{date}}

Batches tracked: {{e.g. "S26 (post-demo, day +12) · F26 (in session) · W27 (forming, 1 company visible)"}}
Coverage: Southeast Asia · Korea · Australia · Hong Kong · Taiwan · Japan · China
Universe: {{n}} companies · {{new}} new this week · {{changed}} materially changed · {{seen}} unchanged (not shown) · {{suppressed}} suppressed after a "no"

## Summary
| # | Company | Batch | What it does | Why included | Region | Tier | Status | Best warm path |
|---|---|---|---|---|---|---|---|---|
| 1 | **Hebbian Robotics** | S26 | Data-quality SDK for physical-AI video | A · Company based in Singapore; both founders NUS/NTU + Singapore roles | SEA | Confirmed 86 | New · in Affinity, no contact | Chris → (name) via (source) |

"Why included" always names the criterion letter and the fact: **A** company based in region, **B** stated nationality or origin, **C** founder currently based in region, **D** formative ties (national service, school), **E** worked in region or at a regional employer, **F** market or operations in region.

## Entries (Confirmed first, then Likely)

### 1. {{Company}} — {{batch}} · {{phase}}
- **Product:** one sentence. **Category:** {{tags}}. **Team size:** {{n}}.
- **Included because:**
  - Company — {{criterion letter · label · region}} ({{source}}), or "no company-level tie".
  - {{Founder 1}} — {{criterion letter · label · region}} ({{source with dates}}). If nationality: "B · Vietnamese, stated in YC profile". If proxy: "D · NUS undergraduate and Singapore Armed Forces, origin proxy". If nothing: "no personal tie stated".
  - {{Founder 2}} — …
- **Founders:** Name (role) — current role and location. [LinkedIn] [Harmonic]
- **Current location:** company {{hq}}; founders {{…}} (observed {{date}}).
- **Why it might fit:** two sentences against `thesis_notes`. Say plainly if it does not fit.
- **Known status:** New / Previously seen ({{date}}) / Known — Affinity ({{met or contacted, date, by whom}}), Harmonic list {{name}}, Drive folder.
- **What changed (if "changed"):** the diff fields.
- **Links:** website · YC profile · Harmonic · Affinity.
- **Outreach draft (optional, never sent):** 3–5 sentences, facts only from the evidence above, referencing the warm path if any.

## Probe: next batch
{{"W27: Harmonic already lists N company(ies) declaring W27: …" or "no signals yet"}}

## Appendix A — Excluded or Weak (one line each)
| Company | Batch | HQ | Founders' stated locations | Note (e.g. "no regional tie stated", "Korean-American: ethnicity descriptor, not nationality") |

## Appendix B — Run log
- Harmonic cohort queries: {{code → count, has_next, cohort URN or "not in Harmonic"}}
- YC directory snapshots: {{slug → total, added, removed, changed}}
- Enriched this run: {{n}} companies in {{k}} Harmonic calls; unenriched carried to next run: {{…}}
- Feedback: `python3 ~/.claude/skills/yc-nexus-scout/scripts/ycscout.py feedback --key <domain> --verdict worth_meeting|maybe|no`
