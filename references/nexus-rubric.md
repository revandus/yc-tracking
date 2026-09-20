# Geographic-nexus rubric (SEA + Korea)

Goal: an evidence-backed, auditable statement of a founder's or company's tie to Southeast Asia or Korea. Every point comes with a citation of the field it came from. Score is per company (best-supported view across founders), capped at 100.

## Absolute rules
- Never infer origin, nationality or ethnicity from a person's name, photo, language, or surname. Such a guess scores zero and must not appear in evidence.
- Only stated facts count: a location string on a role, a school name, an employer with a stated location, a self-description in a bio or YC blurb.
- Evidence strings are written as `source › field: value (dates)`, e.g. `Harmonic › education: National University of Singapore (2019–2023)`.
- Old evidence decays. Multiply a founder-level item by `0.5 ** (years_since_end / recency_halflife_years)` where `years_since_end` counts from the item's end date to today (current roles decay 0).

## Evidence types and base points

| Type | Base | Source fields | Notes |
|---|---:|---|---|
| Company HQ in SEA/Korea | 40 | Harmonic `location.country/city`; YC `all_locations` | Counts once |
| Founder current location in SEA/Korea | 35 | Harmonic person `location`; current role location | Per founder, take max |
| Explicit self-description of origin or base | 35 | YC `long_description`, Harmonic description, founder headline | Must quote the phrase |
| National service or government body in SEA/Korea | 30 | experience company name in `geo.national_service` | Strong stated-location evidence |
| Founder education at SEA/Korea institution | 25 | education school in `geo.institutions`, or school name containing a country/city | Cap 35 across all founders |
| Founder work experience located in SEA/Korea | 20 | experience `location` contains country/city | Per distinct employer, cap 30 |
| Work at SEA/Korea-headquartered employer (any location) | 15 | experience company in `geo.employers_hq` | Cap 20 |
| Prior company founded with HQ in SEA/Korea | 15 | experience roleType FOUNDER with location | |
| Stated customers, market or operations in SEA/Korea | 20 | descriptions mention the region as market or ops | Company-level |
| Another founder on the team already qualifies Strong | 10 | | Team-level bonus |

Penalties: HQ listed as "Remote" or missing with no founder evidence, 0 points (not negative). Evidence older than 12 years after decay contributes almost nothing by construction.

## Tiers
- **Strong** ≥ 60: appears in the main report.
- **Probable** 35–59: appears in the main report below Strong entries, flagged for a human check.
- **Weak** < 35: appendix only, one line each.

## Output record
```json
{
  "nexus_score": 78, "nexus_tier": "strong",
  "nexus_evidence": [
    "Harmonic › company.location: Singapore",
    "Harmonic › founder Kingston Kuan › education: National University of Singapore (2019–2023)",
    "Harmonic › founder Kingston Kuan › experience: Jane Street, Singapore (2023–2025)",
    "Harmonic › founder Brandon Ong › experience: Republic of Singapore Air Force (2015–2017)"
  ],
  "current_location": {"company": "Singapore", "founders": {"Kingston Kuan": "Singapore", "Brandon Ong": "Singapore"}},
  "nexus_countries": ["Singapore"],
  "evidence_observed_at": "2026-09-22"
}
```

## Worked contrast
- A founder with a Vietnamese-looking surname, MIT degree, US roles, US HQ: **score 0**, appendix, evidence list empty. Name is not evidence.
- A founder with no regional surname, HQ in Austin, but "Ho Chi Minh City" on two engineering roles 2018–2022: work-experience points with decay, likely Probable. Human check flagged.
