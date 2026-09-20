# Geographic-nexus rubric

Coverage: **Southeast Asia** (Singapore, Indonesia, Vietnam, Thailand, Malaysia, Philippines, Cambodia, Myanmar, Laos, Brunei, Timor-Leste), **Korea**, **Australia**, **Hong Kong**, **Taiwan**, **Japan**, **China**. Vocabularies live in `config.json › geo.regions`.

## The inclusion test
A company is included when at least one of these is true:

| # | Criterion | How it is established | Tier if this is the only evidence |
|---|---|---|---|
| A | **Company is based in a coverage region** | Harmonic `location`, YC `all_locations`, or a stated HQ in the description | Confirmed |
| B | **A founder's stated nationality or origin is in a coverage region** | A demonym or origin phrase used as identity in the YC blurb, Harmonic description, founder headline or bio: "Vietnamese founder", "I am Taiwanese", "born and raised in Jakarta". See `geo.demonym_rules`. | Confirmed |
| C | **A founder is currently based in a coverage region** | Harmonic person `location` or the location on their current role | Confirmed |
| D | **Formative ties**: national service, high school, or undergraduate degree in a coverage region | education and experience entries | Likely (origin proxy) |
| E | **Worked in a coverage region** or at an employer headquartered there | experience `location`, employer in `employers_hq` | Likely |
| F | **Market or operations** in a coverage region | descriptions naming the region as customers or operations | Likely |

Anything else is excluded and goes to the appendix with an empty evidence list.

## Absolute rules
- Nationality is never inferred from a name, photo, surname or language. Criterion B needs a quotable phrase. If the phrase is an ethnicity descriptor in a diaspora context ("Korean-American", "Chinese-Canadian") or a language, it is **not** B; record it under D or E only if other facts support it, otherwise ignore.
- Every evidence string names the source, the field, the value, the dates, and the region: `Harmonic › founder Kingston Kuan › education: National University of Singapore (2019–2023) → Southeast Asia`.
- Region attribution comes from the vocabulary hit, not from judgement. A founder who studied at UNSW and worked at Grab has evidence in two regions; list both.
- Recency decay applies to D and E only: multiply by `0.5 ** (years_since_end / recency_halflife_years)`. A, B and C do not decay.

## Points (for ordering and confidence; the tiers gate the report)

| Criterion | Base | Cap |
|---|---:|---:|
| A company based in region | 40 | 40 |
| B stated nationality or origin | 40 | 40 per founder, 60 team |
| C founder currently based in region | 35 | 35 per founder |
| D national service | 30 | 30 |
| D high school or undergraduate degree | 25 | 35 across founders |
| E work located in region | 20 per distinct employer | 30 |
| E employer headquartered in region, role elsewhere | 15 | 20 |
| F market or operations in region | 20 | 20 |
| Second founder independently qualifying | 10 | 10 |

Tiers: **Confirmed** ≥ 60 or any of A, B, C present; **Likely** 35–59 or only D/E/F present; **Weak** < 35, appendix only.

## Output record
```json
{
  "included": true,
  "inclusion_reasons": [
    {"who": "company", "criterion": "A", "label": "Company based in Singapore", "region": "Southeast Asia", "source": "Harmonic › location.country: Singapore"},
    {"who": "Kingston Kuan", "criterion": "D", "label": "Studied at NUS; Singapore-located roles at Jane Street", "region": "Southeast Asia", "source": "Harmonic › education (2019–2023); experience: Jane Street, Singapore (2023–2025)"},
    {"who": "Brandon Ong", "criterion": "D", "label": "Republic of Singapore Air Force (2015–2017); PhD NTU", "region": "Southeast Asia", "source": "Harmonic › experience; education"}
  ],
  "primary_reason": "A · Company based in Singapore",
  "nexus_score": 86, "nexus_tier": "confirmed",
  "regions": ["Southeast Asia"],
  "current_location": {"company": "Singapore", "founders": {"Kingston Kuan": "Singapore", "Brandon Ong": "Singapore"}},
  "evidence_observed_at": "2026-09-22"
}
```

## Worked contrasts
- Founder with a Vietnamese-looking surname, MIT, US roles, US HQ, no stated origin: **excluded**, empty evidence. A name is not evidence.
- Founder whose YC blurb says "grew up in Ho Chi Minh City", now in New York, US HQ: **Confirmed via B** (stated origin), primary reason "B · Vietnamese origin, stated in YC profile".
- Founder with Tsinghua undergraduate and Tencent roles in Shenzhen, now in San Francisco, US HQ, no stated nationality: **Likely via D and E**, primary reason "D · Undergraduate at Tsinghua (proxy for Chinese origin)". The write-up says "proxy", not "Chinese".
- Company HQ Sydney, both founders American by stated bio: **Confirmed via A**, reason "A · Company based in Australia"; founders' individual lines say "no personal tie stated".
