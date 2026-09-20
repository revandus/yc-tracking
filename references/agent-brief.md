# Enrichment agent brief (yc-nexus-scout)

Location: `~/Projects/yc-tracking/references/agent-brief.md` (symlinked skill path `~/.claude/skills/yc-nexus-scout/references/agent-brief.md`).

You are enriching one chunk of Y Combinator companies and applying the geographic-nexus inclusion test. Work only from the tools named here. Do not browse LinkedIn or the web.

## Inputs
- Your chunk file: a JSON array of companies with `key`, `name`, `harmonic_id` (may be null), `domain`, `hq`, `yc_url`, `one_liner`, `fingerprint`.
- Rubric: `~/Projects/yc-tracking/references/nexus-rubric.md` (read it first).
- Geo scan helper: `python3 ~/Projects/yc-tracking/scripts/ycscout.py geo-scan "<text>"` returns vocabulary hits grouped by region and category. Use it on every founder's education + experience + location text and on the company description.

## Tool calls
1. For companies with `harmonic_id`: call the Harmonic MCP tool `get_companies` with `ids` = up to 6 ids at a time and `field_groups` = ["name_id_description_headcount_website","location","founders_ceo","external_profiles","date_added_to_harmonic","notes_and_list_membership","contact"]. The `contact` group returns company emails/phone and each founder's `contact.primaryEmail`; record them (see output). Large results are saved to a file; read that file in chunks with Read (offset/limit) until you have covered every company in the call.
2. For companies without `harmonic_id`: call `get_companies` with `identifiers` = [{"website_domain": "<domain>"}] (up to 6 per call, same field_groups). If no record resolves, record the company as `unenriched` with reason.
3. If a founder has no education and no experience in the result, call `get_people` with `linkedin_urls` = [their LinkedIn URL] and `field_groups` = ["basic","experience","education","location"].

## Decide per company (rubric criteria)
A company is `included` when at least one criterion holds: A company based in a coverage region (Harmonic location or stated HQ); B a founder's stated nationality/origin in a region (quotable phrase; ethnicity descriptors like "Korean-American" do NOT count); C a founder currently based in a region (person location or current role location); D formative ties (national service, high school, undergraduate degree in region); E worked in a region or at an employer headquartered there; F market or operations in a region.
Tier: `confirmed` if any of A/B/C; `likely` if only D/E/F; otherwise not included.
Never infer nationality from names, photos or language. Every reason must cite source field, value and dates, and name the region.

## Output
Write ONE JSON file: `~/Projects/yc-tracking/state/candidates/<BATCH>/enriched-<chunk>.json` with this shape:
{
  "chunk": "<BATCH>-<nn>", "enriched": <count>, "unenriched": [{"key":..., "name":..., "reason":...}],
  "companies": [
    {
      "key": "...", "name": "...", "batch": "<BATCH>", "harmonic_id": 123, "domain": "...", "website": "...", "yc_url": "...",
      "description": "one or two sentences, what it does",
      "hq": "City, Country or null", "headcount": 3, "company_emails": ["hello@company.com"], "phone": "+65 ... or null",
      "founders": [
        {"name": "...", "title": "...", "linkedin": "https://linkedin.com/in/...", "email": "founder@company.com or null", "harmonic_person_id": 123,
         "current_location": "...", "current_role_location": "...",
         "education": ["School (start-end, degree)"], "experience": ["Company, Location (start-end, title)"],
         "reason": {"criterion": "B", "label": "Vietnamese, stated in description", "region": "Southeast Asia", "source": "Harmonic > description: '...' "} or {"criterion": null, "label": "no personal tie stated"}}
      ],
      "company_reason": {"criterion": "A", "label": "Based in Singapore", "region": "Southeast Asia", "source": "Harmonic > location.country"} or null,
      "included": true, "tier": "confirmed|likely", "primary_reason": "A · Based in Singapore", "regions": ["Southeast Asia"],
      "harmonic_lists": ["list names from notes_and_list_membership, if any"],
      "fingerprint": "from the chunk file"
    }
  ]
}
Include EVERY company from the chunk in `companies` (excluded ones with "included": false, tier null, and founders with reason label "no personal tie stated"). Keep education/experience arrays to the 6 most relevant lines each. Do not write anything else to disk. Your final message: chunk id, counts (enriched, included confirmed, included likely, excluded, unenriched), and the path of the file you wrote.
