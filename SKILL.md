---
name: aesthetic-case-writer
description: Write journal-ready medical-aesthetics (医美) case reports and case series manuscripts in English (default) from a clinician's case notes, photos and data — topic triage and PubMed novelty check, structured intake, statistics for case series and split-face (半脸对照) series, CARE/PROCESS-structured drafting, and an interactive self-review that walks the clinician through every CARE or PROCESS checklist item by asking questions. Covers injectables (HA, PLLA/童颜针, toxin/肉毒), energy-based devices (光电, RF/热玛吉, picosecond), skin boosters, complications (nodules, Tyndall, vascular occlusion, PIH). Use when the user wants to 写病例报告 / case report / case series / 病例系列 / 投稿 / CARE清单 / PROCESS清单, asks whether a 医美病例值得写, or wants to turn 病程/病例/随访数据 into a manuscript. For a presentation deck of the case use medical-aesthetics-report instead (this skill can hand off to it).
---

# Aesthetic Case Writer

Turn aesthetic-medicine cases into submission-ready **manuscripts** (not slides). Two modes:
**case_report** (one patient, CARE) and **case_series** (≥ 3 patients or a split-face series, PROCESS-based).
Write the manuscript in English unless the user asks otherwise; talk to the user in their language.

## Iron rules
1. **No fabrication.** Every fact and number comes from the clinician's material or `analysis/results.json`. Missing → ask, or mark `[TBC: …]` in the draft. Never estimate parameters, dates, doses or outcomes.
2. **Every reference verified** (PMID/DOI resolves and says what is cited). Unverified → do not cite.
3. **De-identified.** Day offsets instead of dates; no names, record numbers or clinic names in text; identifiable faces only with publication consent. Warn the user not to paste identifiable data into public AI tools.
4. **Claims match the design.** Case report: descriptive, no p-values. Series without control: no comparative/causal claims.
5. **The clinician decides.** Offer options at decision points; do not silently choose the story, the target journal, or what to omit.

## Workflow

Create a working folder (default `./<case_id>/`) with `case.json` (or `series_meta.json` + data), `analysis/`, `figures/`, `review/`, `manuscript.md`.

### Step 0 — Triage (always first)
Read `references/topic-triage.md`. Classify the case into one of the five categories, apply the publishability test, and run the novelty search. Present to the user: category, prior reports found (with verified PMIDs), the proposed **key message**, and report-vs-series recommendation. If the only message is "it worked", say so plainly and propose what would make it publishable (series, controlled design, longer follow-up). Get the user's go/no-go and mode.

### Step 1 — Intake
Read `references/case-schema.md` and `references/aesthetic-reporting.md`. Extract the raw material into `case.json` / `series_meta.json`. Then list what is missing, grouped and prioritised (critical first: parameters, timeline, outcomes + assessor, adverse events, consent), and ask for it — at most ~5 questions per round. Record unresolved gaps in `missing`.

### Step 2 — Analysis
- **Case report**: build the timeline figure — `python scripts/timeline_figure.py case.json --out figures/timeline.png`; tabulate baseline vs follow-up values; plan the photo grid (same view across timepoints).
- **Case series / split-face**: read `references/statistics.md`, write the config, run `python scripts/series_stats.py data.csv config.json --out analysis/`. Show the user the key results and every warning **before drafting**, and check the four common errors listed there.

### Step 3 — Draft
Read `references/writing-guide.md`. Start from `assets/templates/case_report.md` or `case_series.md`; take declarations from `assets/templates/statements.md`. Write `manuscript.md`. Put `[TBC: …]` wherever information is missing. Keep to the target journal's limits if one is chosen.

### Step 4 — Automated checks
```bash
python scripts/trace_numbers.py manuscript.md --sources case.json analysis/results.json [other source files] --out review/trace.md
python scripts/deid_check.py manuscript.md case.json --out review/deid.md
```
Fix or explain every unmatched number and every de-identification flag before Step 5.

### Step 5 — Interactive checklist self-review (CARE or PROCESS)
This is a conversation with the clinician, not a silent pass. Use `scripts/checklist_session.py` to keep state (resumable across sessions).

1. `python scripts/checklist_session.py init --type care|process --out review/checklist_state.json`
2. **Pre-scan**: read the manuscript against every item. For each item clearly covered, run `set <id> --status reported --location "<Section ¶n>"`. Be strict: an aesthetic extension that is absent (e.g., dilution, Fitzpatrick type, who rated GAIS) means the item is not fully reported.
3. **Show progress** (`status`), then work through open items with `next --n 3`: items come grouped by section. For each batch:
   - Tell the user briefly what the item requires and what is currently missing in *their* manuscript (quote the gap concretely: "Methods ¶2 gives the PLLA volume but not the dilution or hydration time").
   - Ask the item's suggested question, adapted to the case. Use AskUserQuestion when the answer is a choice (e.g., blinded rater? yes / no / not recorded; consent covers facial photos? yes / no / unsure); ask in plain text when the answer is free text (parameters, history). Never more than 3–4 questions at a time.
   - Answer supplied → revise the manuscript with **only** that information, then `set <id> --status added --location "..."`.
   - Information does not exist → `set <id> --status not_available --note "..."`; add the gap to the limitations if it matters.
   - Not applicable → `set <id> --status na --note "..."` (e.g., no diagnostic challenges).
   - Critical items (consent, intervention parameters, adverse events, outcome assessor, ethics for off-label) left `not_available`: warn clearly that editors may reject, and suggest how to obtain the information.
4. For case series, finish with the JBI self-appraisal: walk the 10 questions with the user (`appraise <n> --answer yes|no|unclear|na --note ...`) and turn each "no/unclear" into an explicit limitation sentence.
5. `export review/checklist_state.json --md review/checklist.md --docx review/checklist.docx`. Remind the user to transfer locations (page/line numbers) onto the journal's official checklist after final formatting.

Re-run Step 4 after the revisions.

### Step 6 — Deliver
- `pandoc manuscript.md -o manuscript.docx` (add `--reference-doc` if the user has a journal template).
- Hand over: `manuscript.docx`, `review/checklist.docx`, figures, `review/trace.md`, cover letter (from statements.md), and a short list of any remaining `[TBC]` items and open critical checklist items.
- Optional: `python scripts/to_subject_json.py case.json --out <deck_dir>/subjects/<id>/subject.json` and continue with the **medical-aesthetics-report** skill for a presentation deck of the same case.

## Resources
- `references/topic-triage.md` — five publishable categories, publishability test, PubMed novelty search.
- `references/case-schema.md` — `case.json` and `series_meta.json` fields.
- `references/aesthetic-reporting.md` — injectable/device parameters, photography, scales, AEs, confounders, consent.
- `references/statistics.md` — analysis by design, common errors, `series_stats.py` config, blinded rating, reporting format.
- `references/writing-guide.md` — section intent, style, candidate journals, AI-use policy.
- `assets/checklists/` — CARE and PROCESS items with aesthetic extensions and suggested questions (consumed by `checklist_session.py`).
- `assets/templates/` — manuscript skeletons and standard statements.
- `assets/examples/plla_nodule_case.json` — worked example input for demos and testing.
