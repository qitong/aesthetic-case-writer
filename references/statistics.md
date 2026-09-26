# Statistics for aesthetic case reports and case series

## Choose the analysis by design

| Design | Do | Do not |
|---|---|---|
| Single case report | Timeline figure; baseline vs follow-up values in a small table; standardised photo grid; describe changes | p-values, "significant", percentages of one patient |
| Case series (single arm) | Descriptives (median/IQR for ordinal, mean ± SD for continuous); responder rate with exact 95% CI; within-patient change vs baseline (Wilcoxon signed-rank; paired t only if roughly normal); duration of effect (Kaplan–Meier); AE rates with exact CI | Causal or comparative claims without a control |
| Split-face series | Everything above per side, plus **test minus control** on change from baseline (paired); state allocation method | Independent-samples tests; ignoring that sides share a patient |

## The four errors to check in any AI or author output
1. Split-face or before/after treated as independent samples → must be paired.
2. Ordinal scales (GAIS, severity grades) summarised with means and t-tests → medians/IQR, Wilcoxon, proportions.
3. Several time points tested separately without adjustment → adjust (Holm is applied by the script) or pre-specify one primary time point.
4. p-values alone → report effect size and 95% CI; with small n the CI is the message.

Also: zero events ≠ zero risk. With 0/n events the exact 95% upper bound is ≈ 3/n (20 patients → up to ~15%).

## `series_stats.py` config

```jsonc
{
  "design": "split_face",                 // single_arm | split_face
  "timepoints": ["D0", "D7", "D30", "D90"],
  "baseline": "D0",
  "sides": {"T": "test", "C": "control"}, // column suffixes for split_face
  "demographics": {"continuous": ["age"], "categorical": ["fitzpatrick", "sex"]},
  "measures": [
    {"name": "tewl", "label": "TEWL (g/m²/h)", "type": "continuous", "lower_is_better": true},
    {"name": "ery",  "label": "Erythema score (0–4)", "type": "ordinal", "lower_is_better": true}
    // columns default to "{name}_{tp}" (single_arm) or "{name}_{tp}_{side}" (split_face);
    // override with "pattern": "..." or explicit "columns": {"D0": "col", "D0_T": "col", ...}
  ],
  "rates": [{"label": "GAIS improved at D90", "column": "gais_D90_T", "rule": "<=3"}],   // rule applied to values; omit for 0/1 columns
  "adverse_events": [{"label": "PIH", "column": "ae_pih"}],                             // 0/1 columns
  "duration": {"label": "Duration of improvement", "time": "months", "event": "lost", "unit": "months"},
  "raters": [{"label": "Blinded GAIS D90", "cols": ["rater1", "rater2"], "type": "ordinal"}]  // ordinal→weighted kappa, nominal→kappa, continuous→ICC(2,1)
}
```

Run: `python scripts/series_stats.py data.csv config.json --out analysis/` →
`analysis/results.json` (the only source of numbers for the Results section), `results.md`, `figures/*.png`.

Read `results.json` warnings. If n < 10 per group, say in the manuscript that inferential statistics are
exploratory. If a measure has many ties (ordinal scales), prefer proportions ("14/20 improved by ≥ 1 grade")
over test statistics in the text.

## Blinded photo rating — how to set it up
1. List all (patient, timepoint, view) photos; assign random codes; shuffle order (seeded, and keep the key).
2. Raters score each coded photo on the scale, or pick the "after" photo from a pair.
3. Merge scores back by code; compute agreement via the `raters` block; use the mean or consensus score as the outcome.
A randomisation table can be generated with a few lines of pandas (`df.sample(frac=1, random_state=SEED)`); save the key separately from what raters see.

## Reporting format
- "TEWL decreased from 19.7 ± 4.9 to 12.4 ± 4.9 g/m²/h at Day 90 on the test side (mean change −7.3; 95% CI −7.9 to −6.7)."
- "18/20 patients (90%; 95% CI 68–99%) were rated improved on GAIS by the blinded evaluator."
- "No PIH occurred (0/20; 95% CI 0–17%)."
- p-values: exact to 3 decimals, "< 0.001" below that; always next to an effect estimate.
