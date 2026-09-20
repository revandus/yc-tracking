# YC batch lifecycle (as the skill models it)

YC runs four batches a year since 2025: **W** Winter (Jan–Mar), **X** Spring (Apr–Jun), **S** Summer (Jun–Sep), **F** Fall (Oct–Dec). Codes are letter plus two-digit year: W26, X26, S26, F26, W27. Public directory slugs: `winter-2026`, `spring-2026`, `summer-2026`, `fall-2026`. Harmonic labels cohorts `Y Combinator - F26` and resolves the natural-language phrase "Y Combinator Fall 2026 (F26)" to that cohort.

Phases per batch, computed by `ycscout.py batches` from `config.json`:

| Phase | Window | What shows up |
|---|---|---|
| future | before forming window | nothing, but Harmonic may already have a cohort with 1–5 self-declared companies. The skill probes the next two batches every week. |
| forming | `forming_lead_days` (default 90) before start → start | founders add "Y Combinator, F26" to profiles; Harmonic tags companies; YC directory lists some early. |
| in_session | start → demo day | steady weekly additions, pivots, name changes, HQ changes. |
| post_demo | demo day → +90 days | remaining companies go public; fundraising announcements; founders update locations. |
| archived | after that | not tracked. Companies stay in the registry. |

Observed on 2026-09-20: S26 demo day was 2026-09-10 (post_demo); F26 runs 2026-10-01 → demo 2026-12-02 (forming, 127 companies already tagged in Harmonic, 79 public in the YC directory); W27 already had 1 company tagged in Harmonic (probe hit).

When YC publishes exact dates, add them to `config.json › batches.overrides` as `"F27": {"start": "...", "demo": "..."}`. Everything else derives automatically.
