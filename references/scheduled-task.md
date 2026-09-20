# Weekly unattended run — scheduled-task prompt

Suggested `taskId`: `yc-nexus-scout-weekly`, cron `0 8 * * 1` (Mondays 8:00 local). Scheduled tasks run while the Claude desktop app is open; a missed run fires on next launch.

Prompt:

---
Run the `yc-nexus-scout` skill (Skill tool, name `yc-nexus-scout`) end to end in **run** mode. This is an UNATTENDED run: do not ask questions and never wait for input. Use the batches returned by the skill's `batches` command for today, including the probe batches.

Follow the skill's pipeline exactly: universe from Harmonic cohort queries and the YC directory snapshots, classify against the registry, enrich only new or changed companies, apply the nexus rubric with cited evidence, check known/seen status in Affinity, Harmonic lists and the Drive Companies registry, find warm paths for Strong and Probable entries, then write the report.

Deliver per `config.json › report.delivery`. Never send outreach; drafts stay in the report. In your final message paste the Summary table and the Probe section, and list any batch whose Harmonic cohort query did not resolve.
---
