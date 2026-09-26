# Input schema

Two inputs, depending on mode. Build them from the clinician's raw material (case notes, photos,
instrument exports). **Only transcribe what the clinician provided. Unknown → leave the field out
and record it in `missing` — never estimate or invent.**

## Case report → `case.json`

```jsonc
{
  "case_id": "plla_nodule_01",
  "mode": "case_report",
  "category": "complication",        // complication | new_indication | special_population | diagnostic_imaging | long_term
  "working_title": "Late-onset nodules after poly-L-lactic acid injection managed with ...",
  "key_message": "One sentence: what colleagues learn from this case.",
  "novelty": {"search_date": "2026-09-26", "query": "...", "similar_reports": 4, "what_is_new": "..."},

  "patient": {
    "initials": "",                   // for internal use only; never printed in the manuscript
    "age": 38, "sex": "female", "fitzpatrick": "IV", "ethnicity": "East Asian",
    "goal": "Restore mid-face volume",
    "medical_history": "No systemic disease",
    "medications": ["none"],          // flag anticoagulants, isotretinoin, GLP-1 RA, immunomodulators
    "aesthetic_history": [{"treatment": "HA filler", "area": "tear trough", "when": "18 months before"}],
    "bdd_screen": "negative (BDDQ)"   // or "not performed"
  },
  "presenting_concern": "...",
  "clinical_findings": "...",
  "diagnosis": {"final": "...", "differential": ["...", "..."], "methods": ["high-frequency ultrasound 18 MHz"], "challenges": ""},

  "interventions": [
    {"day": 0, "type": "injectable", "summary": "PLLA to bilateral mid-face",
     "product": "poly-L-lactic acid (trade name, manufacturer, country)", "lot": "",
     "reconstitution": "8 mL sterile water + 1 mL lidocaine 2%, hydrated 48 h", "dose": "1 vial per side",
     "plane": "supraperiosteal", "needle": "25G cannula", "technique": "fanning, retrograde", "areas": "zygomatic, submalar",
     "operator": "dermatologist, 8 years injecting experience"},
    {"day": 0, "type": "energy", "device": "model, manufacturer", "wavelength": "1064 nm", "fluence": "...", "pulse_width": "...",
     "spot_size": "...", "passes": 2, "cooling": "...", "endpoint": "mild erythema"},
    {"day": 75, "type": "management", "summary": "intralesional triamcinolone 10 mg/mL, 0.1 mL per nodule"}
  ],
  "timeline": [
    {"day": 0,   "label": "PLLA session 1", "kind": "treatment"},
    {"day": 60,  "label": "Palpable nodules noted", "kind": "event"},
    {"day": 75,  "label": "Ultrasound + intralesional steroid", "kind": "management"},
    {"day": 180, "label": "Final follow-up", "kind": "followup"}
  ],
  "outcomes": [
    {"measure": "Nodule diameter", "unit": "mm", "tool": "ultrasound", "assessor": "treating physician",
     "timepoints": {"D75": 6.2, "D105": 3.1, "D180": 0}},
    {"measure": "GAIS", "tool": "GAIS 5-point", "assessor": "independent blinded dermatologist", "timepoints": {"D180": "improved"}}
  ],
  "adverse_events": [{"event": "skin atrophy", "onset_day": null, "severity": "", "management": "", "resolved": ""}],  // [] only if the clinician confirms none
  "tolerability": "downtime 2 days; mild bruising",
  "patient_perspective": "",          // quote or paraphrase approved by the patient
  "photos": [{"file": "img/d0_front.jpg", "timepoint": "D0", "view": "frontal", "system": "VISIA 7th gen", "standardised": true}],
  "split_face": null,                 // {"test_side": "right", "control_side": "left", "allocation": "random"} if relevant
  "consent": {"treatment": true, "publication": true, "photos_identifiable": true},
  "off_label": false, "ethics": "",
  "declarations": {"conflicts": "", "funding": "", "ai_use": "drafting assisted by an AI tool; authors verified all content"},
  "missing": ["lot number", "patient perspective"]
}
```

## Case series → `series_meta.json` + data table

`series_meta.json` holds everything that is not per-patient:

```jsonc
{
  "series_id": "plla_gpl1_series",
  "mode": "case_series",
  "design": "retrospective",          // retrospective | prospective
  "split_face": false,
  "sites": ["clinic A", "clinic B"], "period": "2024-01 to 2025-12",   // year-month is fine; no patient-level dates
  "consecutive": true,
  "identification": "EMR search for all PLLA treatments in patients on GLP-1 RA",
  "inclusion": ["..."], "exclusion": ["..."], "washout": "no filler 12 months, no toxin 4 months",
  "protocol": { /* same parameter fields as a case-report intervention */ },
  "operators": {"n": 3, "experience": "5–12 years"},
  "outcome_definitions": {"primary": "GAIS improved at M6 by blinded rater", "responder": "GAIS 1–3 ('very much improved' to 'improved')"},
  "photography": "VISIA, fixed distance, frontal + 45° + 90°",
  "ethics": "", "consent": "", "declarations": {},
  "losses_to_follow_up": "", "missing": []
}
```

The data table (CSV/XLSX, one row per patient, **no names or dates**) plus an analysis config feed
`scripts/series_stats.py`. Column conventions and the config are in `references/statistics.md`.

## Photos

Keep originals untouched. Work on copies: crop to identical framing per view, strip EXIF, remove
jewellery/tattoos/background. Record per photo: timepoint, view, lighting/system, whether standardised.
Unstandardised photos can still be used but must be described as such in the limitations.
