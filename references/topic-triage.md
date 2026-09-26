# Topic triage — is this case worth writing?

Run this before any drafting. A case is publishable when it carries **new knowledge**;
"a good result with nice before/after photos" alone is almost never accepted.

## The five publishable categories in aesthetic medicine

| Category | Typical examples | Notes |
|---|---|---|
| Complication and its management | vascular occlusion / skin necrosis, HA delayed inflammatory reaction, PLLA or HA nodules / granuloma, Tyndall effect, toxin spread (ptosis, diplopia), energy-device burns or PIH, thread infection, removal of illicit fillers (e.g., polyacrylamide gel) | Most common accepted type. Value rises with: unusual presentation, imaging-guided diagnosis, a management approach with follow-up, causality discussion |
| New indication / area / technique | PLLA in neck or hands, microdroplet toxin for sebum/pores, toxin for rosacea flushing, ultrasound-guided injection, new combination protocol | Off-label → needs specific consent and usually ethics approval; say so in the manuscript |
| Special population | facial volume loss after GLP-1 RA weight loss, Fitzpatrick IV–VI (PIH risk), multiple / unknown prior fillers, autoimmune disease, sensitive skin / rosacea, facial palsy asymmetry, keloid tendency | Evidence base is mostly Fitzpatrick I–III and industry RCTs — local population data is a genuine gap |
| Diagnostic / imaging value | high-frequency ultrasound to localise filler, vessels or nodules; MRI to identify foreign material | Include images with scale and probe frequency |
| Long-term follow-up | ≥ 2-year durability, imaging evidence of product degradation, repeated-treatment trajectories | Clinics with long-term returning patients have an advantage here |

## Quick publishability test (ask the clinician)

1. In one sentence, what would a colleague learn from this that they did not know? If the answer is "the treatment works", stop — suggest a case series or a controlled design instead.
2. Is the documentation complete enough? (standardised photos, full parameters, follow-up ≥ the clinically relevant horizon, consent for publication)
3. Has it been reported before, and how often? → novelty search below.
4. Report or series? One striking case → case report. ≥ 3–5 comparable patients with the same intervention/event → case series (usually stronger). Same patients with a within-patient control → split-face series.

## Novelty search

Use a PubMed tool/skill if available; otherwise E-utilities:

```
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmax=50&retmode=json&term=<QUERY>
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id=<ID,ID,...>
```

Query pattern: `(<material/device synonyms>) AND (<event/indication synonyms>) AND ("Case Reports"[pt] OR case series[tiab])`
e.g. `("poly-L-lactic acid" OR PLLA OR Sculptra) AND (nodule* OR granuloma*) AND ("Case Reports"[pt] OR "case series"[tiab])`

Report back: number of hits, the 3–8 closest reports (first author, year, n, key finding), and a
**what-is-new** statement (population, presentation, diagnostic method, management, follow-up length).
Verify every cited PMID actually exists before it enters the manuscript. Record the query and date
in `case.json.novelty` — journals and reviewers ask.

## Progression path to suggest

single case report → retrospective case series (multi-site if possible) → prospective split-face series → RCT.
Suggest the next rung when the clinician has more patients of the same kind.
