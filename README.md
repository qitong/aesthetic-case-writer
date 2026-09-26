# Aesthetic Case Writer

A Claude Code skill that turns medical-aesthetics cases into journal-ready **case report** and **case series** manuscripts (English by default), with an interactive CARE / PROCESS checklist self-review.

Built for injectables (HA, PLLA, botulinum toxin), energy-based devices (lasers, RF, picosecond), skin boosters and their complications (nodules, Tyndall effect, vascular occlusion, PIH).

## Workflow

0. **Triage** — is the case publishable? Five publishable categories, PubMed novelty search, case report vs case series.
1. **Intake** — structure notes, photos and data into `case.json` / `series_meta.json`; ask for what is missing. Never fabricates.
2. **Analysis** — timeline figure for case reports; `series_stats.py` for case series and split-face series (paired tests, Holm correction, exact CIs, rule of three, Kaplan–Meier, kappa/ICC).
3. **Draft** — CARE / PROCESS-structured manuscript; gaps marked `[TBC]`.
4. **Automated checks** — every number traced to a source file; de-identification scan.
5. **Interactive checklist self-review** — walks the clinician through each CARE or PROCESS item with targeted questions, revises the manuscript with their answers, records status, exports a filled checklist (plus JBI appraisal for series).
6. **Deliver** — manuscript `.docx`, checklist `.docx`, figures, cover letter; optional hand-off to a slide-deck skill.

## Installation

```bash
git clone https://github.com/qitong/aesthetic-case-writer.git ~/.claude/skills/aesthetic-case-writer
pip install pandas numpy scipy matplotlib openpyxl   # pandoc is needed for .docx export
```

Then ask Claude Code, e.g.:

```text
I have a PLLA late-nodule case (notes + photos attached). Is it worth writing up as a case report? If so, draft it and walk me through the CARE checklist.
```

```text
Here is data from 20 split-face patients (picosecond laser + barrier repair on one side). Analyse it and draft a case series.
```

## Contents

- `SKILL.md` — workflow and rules.
- `references/` — topic triage, input schema, aesthetic reporting elements, statistics, writing guide.
- `assets/checklists/` — CARE and PROCESS items with aesthetic extensions and suggested questions.
- `assets/templates/` — manuscript skeletons and standard statements (consent, ethics, AI use, cover letter).
- `assets/examples/plla_nodule_case.json` — a **simulated** teaching case (not a real patient).
- `scripts/` — `series_stats.py`, `checklist_session.py`, `trace_numbers.py`, `deid_check.py`, `timeline_figure.py`, `to_subject_json.py`.

## Notes

- Checklist items are paraphrased from CARE (2013) and the PROCESS guideline; download the official checklist required by your target journal before submission.
- Do not paste identifiable patient data or photos into public AI services. Authors remain responsible for all content; disclose AI use per journal policy.
