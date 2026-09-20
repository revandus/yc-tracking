# yc-tracking

Claude Code skill `yc-nexus-scout`: a weekly scout of live and forming Y Combinator batches for founders and companies with evidence-backed ties to Southeast Asia or Korea, built on Harmonic and the public YC directory. The skill itself is `SKILL.md`.

## Install

```bash
git clone https://github.com/revandus/yc-tracking.git ~/Projects/yc-tracking
mkdir -p ~/.claude/skills && ln -sfn ~/Projects/yc-tracking ~/.claude/skills/yc-nexus-scout
```

Start a new Claude Code session and the skill is available as `yc-nexus-scout`. Run state (`state/`) stays local and is not committed.

## What it needs

Nothing to install. It uses connectors already available in Claude Code (Harmonic, Affinity, Google Drive, Gmail) plus a standard-library Python helper. No API keys, no OAuth grant.

Optional, recommended after the first two weeks: in the Harmonic console create a subscribed **People** saved search (education school = Y Combinator with an end date this year, current role founder, location or education in SEA/Korea) and paste its `urn:harmonic:saved_search:*` into `config.json › harmonic.person_saved_search_urn`. This catches founders who declare a batch on their profile before Harmonic tags their company.

## First run

In Claude Code:

- `use yc-nexus-scout: batches` — shows which batches are tracked today and which are probed.
- `use yc-nexus-scout: run` — first run enriches every company in the tracked batches (a few hundred), so expect it to take a while and to use subagents. Later runs only touch new or changed companies.
- `use yc-nexus-scout: feedback <domain> worth_meeting|maybe|no` — teach it. A `no` hides the company until something material changes.

## Weekly schedule

See `references/scheduled-task.md`. Suggested Monday 8:00 local. Scheduled tasks run while the Claude desktop app is open; a missed run fires on next launch.

## Keeping the calendar right

YC publishes exact start and demo-day dates per batch. Add them to `config.json › batches.overrides`, for example `"W27": {"start": "2027-01-11", "demo": "2027-03-24"}`. Without an override the skill uses the month-day defaults, which are close enough for tracking windows.

## Where things live

- `state/registry.jsonl` — every company ever evaluated, with score, evidence, status and verdicts. This is the dedupe memory; back it up occasionally.
- `state/snapshots/<batch>/` — dated copies of the public YC directory per batch.
- `state/reports/` — weekly reports (also uploaded to Drive › Sourcing Lists › YC Nexus Scout).
- `state/feedback.jsonl` — partner verdicts.

## Helper commands

```bash
python3 ~/.claude/skills/yc-nexus-scout/scripts/ycscout.py --help
```
