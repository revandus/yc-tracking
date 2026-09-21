# Running the scout as a cloud routine

**Live since 2026-09-21.** Routine `YC Nexus Scout Weekly`, id `trig_01JeaAj7RcED3dtuENomZrFz`, model claude-opus-5, cron `7 0 * * 1` UTC (Mondays 08:07 Asia/Singapore). Connectors attached: Harmonic, Affinity, Gmail, Google Drive. Manage at <https://claude.ai/code/routines/trig_01JeaAj7RcED3dtuENomZrFz>. The local desktop scheduled task `yc-nexus-scout-weekly` is PAUSED and kept only as a manual fallback.

A cloud routine runs in Anthropic's cloud, not on your Mac, so it fires whether or not your computer is on. Each run is an isolated session with a **fresh clone of this repository** and no access to your local machine.

## Why the repo had to change

Cloud runs get a clean checkout every time. Anything not committed does not exist for them. Two consequences:

- **Durable state is now tracked in git** (`state/registry.jsonl`, `state/feedback.jsonl`, `state/snapshots/`, `state/drive.json`, `state/harmonic_lists.json`, `state/reports/`). Without these, every weekly run would treat all ~400 companies as new. Scratch (`state/candidates/`, `state/harvest/`) stays ignored.
- **The routine must commit and push its updated state** at the end of each run, or the next run starts from stale memory.

## Prerequisites

1. **The repo must be on GitHub.** The routine clones `https://github.com/revandus/yc-tracking`. Push first.
2. **The connectors must be claude.ai connectors**, connected at <https://claude.ai/customize/connectors>. MCP servers configured locally in Claude Code (`claude mcp add`) cannot be attached to a cloud routine. The routine needs: **Harmonic**, **Affinity**, **Gmail**, **Google Drive**. Calendar and Granola are not used by this skill.
3. The routine needs write access to the repo so it can push updated state.

## Differences from the local run

| | Local scheduled task | Cloud routine |
|---|---|---|
| Runs when the Mac is off | no | yes |
| Needs the desktop app open | yes | no |
| State | read and written in place | cloned, then committed and pushed back |
| Report delivery | file sent in chat, Drive, Gmail draft | Drive, Gmail draft, committed to `state/reports/`, posted in the run log |
| Cron timezone | local | **UTC** |
| Minimum interval | any | 1 hour |

Monday 08:00 Asia/Singapore is **`0 0 * * 1` UTC**. Nudge off the hour to avoid the global :00 pile-up: `7 0 * * 1` is Monday 08:07 Singapore.

## Keeping the two schedules from fighting

Do not leave both the local scheduled task and the cloud routine enabled. They would both append to `state/registry.jsonl` and both write a report for the same date. Pick one. If you keep the local task as a fallback, `git pull --rebase` before running it locally.

## The routine prompt

Paste this as the routine's prompt. It is deliberately self-contained; a cloud session starts with zero context.

---

You are running the weekly YC Nexus Scout. The repository `yc-tracking` is already cloned into your working directory; `cd` to its root (the directory containing `SKILL.md` and `scripts/ycscout.py`) before anything else and use **repo-relative paths throughout**. Do not reference `~/.claude` or any local path; you are in the cloud and no local machine is reachable.

Read `SKILL.md` and follow its pipeline exactly. `references/nexus-rubric.md` defines the inclusion test, `references/agent-brief.md` is the brief for enrichment subagents, `references/report-template.md` documents the report layout. This is an UNATTENDED run: never ask a question, never wait for input.

Steps:

1. `python3 scripts/ycscout.py batches` for today's tracked and probe batches.
2. For each tracked and probe batch: Harmonic `search_companies_natural_language` with the batch's `harmonic_query`, field_groups `name_id_description_headcount_website` and `location`, size 100, following cursors; save each result and run `python3 scripts/ycscout.py harvest <file> --batch <CODE>`; then `snapshot`, `union` and `classify` for that batch. A probe batch with any Harmonic company is treated as forming.
3. Enrich ONLY the companies under `to_enrich`. Harmonic `get_companies` in pages of 6 with field_groups `name_id_description_headcount_website`, `location`, `founders_ceo`, `external_profiles`, `date_added_to_harmonic`, `notes_and_list_membership`, `contact`. Above 40 companies, delegate chunks of 30 to subagents using `references/agent-brief.md`, then `python3 scripts/merge_enriched.py`.
4. Apply the rubric: criteria A to F, tier Confirmed for A, B or C (or rubric points at or above 60), Likely for D, E or F alone. Never infer nationality from a name, photo or language. Thin proxies (one-month internships, employer-name-only hits, exchange semesters) go to the appendix, not the main list.
5. Known status for every main-list company: Affinity `search_companies_top_matches` by domain, then `get_company_info` with field_types `relationship-intelligence` for met / in process / contacted / in CRM, with who and when. Harmonic `get_company_connections` for warm paths.
6. Write `state/candidates/report-data-<date>.json` (keys `main`, `appendix_likely`, `excluded`, `unenriched`, `counts`, `probe_note`, `run_log`), `state/candidates/known-status-<date>.json` and `state/candidates/contacts-<date>.json`, then run `python3 scripts/render_report.py --data … --known … --date <date> --contacts …`. Do not change the report layout; the renderer owns it.
7. Deliver, in this order:
   - Upload `state/reports/<date>.summary.md` to Google Drive with `create_file` into the folder id in `state/drive.json`, using `textContent`, `contentMimeType` `text/markdown` and `disableConversionToGoogleType` true.
   - Create a Gmail **draft** (never send) to christopher.halim@lsip.com with sections 1 to 3 as plain text.
   - Add new main-list companies to the per-batch Harmonic lists cached in `state/harmonic_lists.json`, creating a list for a new batch with the same five fields.
   - `python3 scripts/ycscout.py registry-upsert` for every enriched company, with tier, inclusion reasons, status, fingerprint and report date.
8. Commit and push the updated state so the next run remembers this one:
   `git add state/registry.jsonl state/feedback.jsonl state/snapshots state/reports state/drive.json state/harmonic_lists.json && git -c user.name="YC Nexus Scout" -c user.email="christopher.halim@lsip.com" commit -m "Weekly scout run <date>" && git pull --rebase && git push`
   If the push is rejected, pull with rebase and retry once, then report the failure.

Read `state/feedback.jsonl` before selecting the main list and honour every `no` verdict. If a week has no new or changed companies, still produce the report with the latest-batch spotlight and a one-line note, and still write the run log.

Finish by posting, in the run output: section 1 (latest batch spotlight) and section 2 (new to Lightspeed) of the report as markdown tables, then the run log, then any batch whose Harmonic cohort did not resolve and any company that could not be enriched.

---

## Managing the routine

- List, update or run now: ask Claude Code to use the `schedule` skill, or open <https://claude.ai/code/routines>.
- Deleting a routine can only be done in the web UI at that link.
- To debug a run, ask for `list_runs` then `get_run_log` on the run in question.
