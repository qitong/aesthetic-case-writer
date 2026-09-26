#!/usr/bin/env python3
"""Deterministic statistics for aesthetic case series and split-face series.

Usage:
  series_stats.py DATA.(csv|xlsx) CONFIG.json --out analysis/

Input: one row per patient (wide format). Column names follow a pattern
(default "{name}_{tp}" for single-arm, "{name}_{tp}_{side}" with side T/C for split-face)
or are listed explicitly per measure. See references/statistics.md for the config schema.

Output (in --out):
  results.json   every number the manuscript may quote (the traceability source)
  results.md     human-readable tables
  figures/*.png  trajectory plots, rate plots with CI, Kaplan-Meier curve
"""
import argparse, json, math, sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

C_TEST, C_CTRL, C_ONE = "#0C7A5C", "#9AA5A1", "#0C7A5C"


def r(x, d=2):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), d)


def desc(v):
    v = pd.Series(v).dropna().astype(float)
    if len(v) == 0:
        return {"n": 0}
    q1, med, q3 = np.percentile(v, [25, 50, 75])
    return {"n": int(len(v)), "mean": r(v.mean()), "sd": r(v.std(ddof=1)) if len(v) > 1 else None,
            "median": r(med), "q1": r(q1), "q3": r(q3), "min": r(v.min()), "max": r(v.max())}


def paired(a, b, kind):
    """Compare b - a within patients. kind: continuous | ordinal."""
    d = pd.DataFrame({"a": a, "b": b}).dropna().astype(float)
    n = len(d)
    out = {"n_pairs": n}
    if n < 3:
        out["note"] = "fewer than 3 complete pairs — descriptive only"; return out
    diff = d["b"] - d["a"]
    out["median_diff"] = r(diff.median())
    out["n_improved_or_changed"] = int((diff != 0).sum())
    if (diff == 0).all():
        out["note"] = "all differences are zero"; return out
    w = stats.wilcoxon(d["b"], d["a"], zero_method="wilcox", method="approx" if n > 25 else "auto")
    out["wilcoxon_p"] = float(w.pvalue)
    # effect size r = Z / sqrt(N) from normal approximation (ties/zeros handled by scipy's approx)
    wa = stats.wilcoxon(d["b"], d["a"], zero_method="wilcox", method="approx")
    z = getattr(wa, "zstatistic", None)
    if z is None:
        z = stats.norm.isf(wa.pvalue / 2) * np.sign(diff.median() or diff.mean())
    out["effect_size_r"] = r(abs(z) / math.sqrt(n), 3)
    if kind == "continuous":
        m, s = diff.mean(), diff.std(ddof=1)
        t = stats.t.ppf(0.975, n - 1)
        out.update({"mean_diff": r(m), "sd_diff": r(s), "ci95_mean_diff": [r(m - t * s / math.sqrt(n)), r(m + t * s / math.sqrt(n))],
                    "paired_t_p": float(stats.ttest_rel(d["b"], d["a"]).pvalue),
                    "cohen_dz": r(m / s, 3) if s > 0 else None})
    return out


def fmt_p(p):
    return "" if p is None else ("<0.001" if p < 0.001 else f"{p:.3f}")


def holm(ps):
    idx = [i for i, p in enumerate(ps) if p is not None]
    order = sorted(idx, key=lambda i: ps[i]); m = len(order); adj = [None] * len(ps); running = 0
    for k, i in enumerate(order):
        running = max(running, min(1.0, (m - k) * ps[i])); adj[i] = running
    return adj


def exact_ci(k, n):
    if n == 0:
        return None
    ci = stats.binomtest(k, n).proportion_ci(confidence_level=0.95, method="exact")
    return [r(ci.low * 100, 1), r(ci.high * 100, 1)]


def apply_rule(series, rule):
    s = pd.to_numeric(series, errors="coerce")
    if rule is None:
        return s
    op, val = None, None
    for o in (">=", "<=", "==", ">", "<"):
        if rule.startswith(o):
            op, val = o, float(rule[len(o):]); break
    if op is None:
        sys.exit(f"Bad rule {rule!r}; use e.g. '>=1' or '<=3'")
    f = {">=": s.ge, "<=": s.le, "==": s.eq, ">": s.gt, "<": s.lt}[op]
    return f(val).where(s.notna())


def kaplan_meier(t, e):
    d = pd.DataFrame({"t": t, "e": e}).dropna().astype(float).sort_values("t")
    times, surv, s, atrisk = [0.0], [1.0], 1.0, len(d)
    for tt, g in d.groupby("t"):
        ev = g["e"].sum()
        if ev > 0 and atrisk > 0:
            s *= 1 - ev / atrisk; times.append(tt); surv.append(s)
        atrisk -= len(g)
    med = next((tt for tt, ss in zip(times, surv) if ss <= 0.5), None)
    return {"n": int(len(d)), "events": int(d["e"].sum()), "median": r(med) if med is not None else None,
            "median_note": None if med is not None else "median not reached", "steps": [[r(a), r(b, 4)] for a, b in zip(times, surv)]}


def cohen_kappa(x, y, weighted=False):
    d = pd.DataFrame({"x": x, "y": y}).dropna()
    cats = sorted(set(d["x"]) | set(d["y"])); k = len(cats); ix = {c: i for i, c in enumerate(cats)}
    O = np.zeros((k, k))
    for a, b in zip(d["x"], d["y"]):
        O[ix[a], ix[b]] += 1
    n = O.sum(); E = np.outer(O.sum(1), O.sum(0)) / n
    W = np.array([[abs(i - j) / (k - 1) if weighted and k > 1 else float(i != j) for j in range(k)] for i in range(k)])
    return {"n": int(n), "kappa": r(1 - (W * O).sum() / (W * E).sum(), 3) if (W * E).sum() > 0 else None,
            "weighting": "linear" if weighted else "none"}


def icc21(M):
    M = np.asarray(M, float); M = M[~np.isnan(M).any(1)]; n, k = M.shape
    gm = M.mean(); msr = k * ((M.mean(1) - gm) ** 2).sum() / (n - 1); msc = n * ((M.mean(0) - gm) ** 2).sum() / (k - 1)
    sse = ((M - M.mean(1, keepdims=True) - M.mean(0, keepdims=True) + gm) ** 2).sum(); mse = sse / ((n - 1) * (k - 1))
    return {"n": int(n), "raters": int(k), "icc_2_1": r((msr - mse) / (msr + (k - 1) * mse + k * (msc - mse) / n), 3)}


def interpret_kappa(k):
    if k is None: return None
    return "poor" if k < 0.2 else "fair" if k < 0.4 else "moderate" if k < 0.6 else "substantial" if k < 0.8 else "almost perfect"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("data"); ap.add_argument("config"); ap.add_argument("--out", default="analysis")
    a = ap.parse_args()
    df = pd.read_excel(a.data) if a.data.endswith((".xlsx", ".xls")) else pd.read_csv(a.data)
    cfg = json.loads(Path(a.config).read_text(encoding="utf-8"))
    out = Path(a.out); (out / "figures").mkdir(parents=True, exist_ok=True)
    design = cfg.get("design", "single_arm"); tps = cfg["timepoints"]; base = cfg.get("baseline", tps[0])
    sides = cfg.get("sides", {"T": "test", "C": "control"})
    res = {"design": design, "n_patients": int(len(df)), "timepoints": tps, "baseline": base, "measures": [], "rates": [],
           "adverse_events": [], "duration": None, "agreement": [], "warnings": []}
    if "demographics" in cfg:
        res["demographics"] = {}
        for col in cfg["demographics"].get("continuous", []):
            res["demographics"][col] = desc(df[col])
        for col in cfg["demographics"].get("categorical", []):
            vc = df[col].value_counts(dropna=False)
            res["demographics"][col] = {str(k): {"n": int(v), "pct": r(100 * v / len(df), 1)} for k, v in vc.items()}
    md = [f"# Analysis results", "", f"Design: {design}; patients: {len(df)}; time points: {', '.join(tps)} (baseline {base})", ""]

    for m in cfg.get("measures", []):
        name, kind = m["name"], m.get("type", "continuous"); label = m.get("label", name)
        pat = m.get("pattern", "{name}_{tp}_{side}" if design == "split_face" else "{name}_{tp}")
        col = lambda tp, side=None: m.get("columns", {}).get(f"{tp}_{side}" if side else tp, pat.format(name=name, tp=tp, side=side))
        mr = {"name": name, "label": label, "type": kind, "lower_is_better": m.get("lower_is_better", False), "descriptives": {}, "comparisons": []}
        groups = list(sides) if design == "split_face" else [None]
        miss = [col(tp, g) for tp in tps for g in groups if col(tp, g) not in df.columns]
        if miss:
            res["warnings"].append(f"{name}: missing columns {miss}"); continue
        for g in groups:
            key = sides[g] if g else "all"
            mr["descriptives"][key] = {tp: desc(df[col(tp, g)]) for tp in tps}
            if base in tps:
                comps = [dict(paired(df[col(base, g)], df[col(tp, g)], kind), group=key, contrast=f"{tp} vs {base}")
                         for tp in tps if tp != base]
                adj = holm([c.get("wilcoxon_p") for c in comps])
                for c, p in zip(comps, adj): c["wilcoxon_p_holm"] = p
                mr["comparisons"] += comps
        if design == "split_face":
            gT, gC = list(sides)
            comps = []
            for tp in tps:
                if base in tps and tp != base:  # change-from-baseline difference, test minus control
                    dT = df[col(tp, gT)] - df[col(base, gT)]; dC = df[col(tp, gC)] - df[col(base, gC)]
                    comps.append(dict(paired(dC, dT, kind), group="test_minus_control", contrast=f"change {base}→{tp}"))
                elif base not in tps:
                    comps.append(dict(paired(df[col(tp, gC)], df[col(tp, gT)], kind), group="test_minus_control", contrast=tp))
            adj = holm([c.get("wilcoxon_p") for c in comps])
            for c, p in zip(comps, adj): c["wilcoxon_p_holm"] = p
            mr["comparisons"] += comps
        if kind == "ordinal" and any("mean_diff" in c for c in mr["comparisons"]):
            res["warnings"].append(f"{name}: ordinal — report medians/IQR and Wilcoxon, not means")
        res["measures"].append(mr)
        # figure
        fig, ax = plt.subplots(figsize=(5.2, 3.4))
        for g in groups:
            key = sides[g] if g else "all"; d = mr["descriptives"][key]
            y = [d[tp].get("median" if kind == "ordinal" else "mean") for tp in tps]
            if kind == "ordinal":
                lo = [d[tp].get("median") - d[tp].get("q1") for tp in tps]; hi = [d[tp].get("q3") - d[tp].get("median") for tp in tps]
            else:
                se = [(d[tp]["sd"] or 0) / math.sqrt(d[tp]["n"]) if d[tp]["n"] else 0 for tp in tps]; lo = hi = se
            c = C_TEST if key in ("test", "all") else C_CTRL
            off = 0 if g is None else (-0.06 if key == "test" else 0.06)
            ax.errorbar([i + off for i in range(len(tps))], y, yerr=[lo, hi], marker="o", capsize=3, color=c, label=key if g else None, lw=2)
        ax.set_xticks(range(len(tps))); ax.set_xticklabels(tps)
        ax.set_ylabel(label + (" (median, IQR)" if kind == "ordinal" else " (mean ± SE)"), fontsize=8)
        ax.spines[["top", "right"]].set_visible(False)
        if design == "split_face": ax.legend(frameon=False, fontsize=8)
        fig.tight_layout(); fig.savefig(out / "figures" / f"{name}.png", dpi=200); plt.close(fig)
        md += [f"## {label} ({kind})", "", "| group | " + " | ".join(tps) + " |", "|---|" + "---|" * len(tps)]
        for key, d in mr["descriptives"].items():
            cell = (lambda s: f"{s['median']} [{s['q1']}–{s['q3']}] (n={s['n']})") if kind == "ordinal" else (lambda s: f"{s['mean']} ± {s['sd']} (n={s['n']})")
            md.append(f"| {key} | " + " | ".join(cell(d[tp]) if d[tp]["n"] else "—" for tp in tps) + " |")
        md += ["", "| group | contrast | n | effect | p (Wilcoxon) | p (Holm) | r |", "|---|---|---|---|---|---|---|"]
        for c in mr["comparisons"]:
            eff = f"mean diff {c['mean_diff']} (95% CI {c['ci95_mean_diff'][0]} to {c['ci95_mean_diff'][1]})" if "mean_diff" in c and kind == "continuous" else f"median diff {c.get('median_diff')}"
            p = c.get("wilcoxon_p"); ph = c.get("wilcoxon_p_holm")
            md.append(f"| {c['group']} | {c['contrast']} | {c['n_pairs']} | {eff} | {fmt_p(p)} | {fmt_p(ph)} | {c.get('effect_size_r', '')} |")
        md.append("")

    def rate_block(items, key, title):
        if not items: return
        md.extend([f"## {title}", "", "| item | k/n | % | exact 95% CI | note |", "|---|---|---|---|---|"])
        for it in items:
            s = apply_rule(df[it["column"]], it.get("rule")).dropna()
            k, n = int(s.sum()), int(len(s))
            row = {"label": it["label"], "column": it["column"], "rule": it.get("rule"), "k": k, "n": n,
                   "pct": r(100 * k / n, 1) if n else None, "ci95_exact": exact_ci(k, n)}
            if k == 0 and n:
                row["rule_of_three_upper_pct"] = r(300 / n, 1)
                row["note"] = f"0/{n}: the true rate could still be up to ~{r(300 / n, 1)}% (rule of three)"
            res[key].append(row)
            md.append(f"| {it['label']} | {k}/{n} | {row['pct']} | {row['ci95_exact']} | {row.get('note', '')} |")
        md.append("")
        fig, ax = plt.subplots(figsize=(5.2, 0.5 + 0.45 * len(res[key])))
        for i, rw in enumerate(res[key]):
            lo, hi = rw["ci95_exact"] or [0, 0]
            ax.errorbar(rw["pct"], i, xerr=[[rw["pct"] - lo], [hi - rw["pct"]]], fmt="o", color=C_ONE, capsize=3)
        ax.set_yticks(range(len(res[key]))); ax.set_yticklabels([rw["label"] for rw in res[key]], fontsize=8)
        ax.set_xlim(0, 100); ax.set_xlabel("% (exact 95% CI)", fontsize=8); ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout(); fig.savefig(out / "figures" / f"{key}.png", dpi=200); plt.close(fig)

    rate_block(cfg.get("rates", []), "rates", "Response rates")
    rate_block(cfg.get("adverse_events", []), "adverse_events", "Adverse events")

    if cfg.get("duration"):
        du = cfg["duration"]; km = kaplan_meier(df[du["time"]], df[du["event"]]); km["label"] = du.get("label", "duration"); km["unit"] = du.get("unit", "")
        res["duration"] = km
        md += [f"## {km['label']} (Kaplan–Meier)", "", f"n={km['n']}, events={km['events']}, median={km['median'] or km['median_note']} {km['unit']}", ""]
        xs, ys = zip(*km["steps"])
        fig, ax = plt.subplots(figsize=(5.2, 3.2)); ax.step(xs, ys, where="post", color=C_ONE, lw=2)
        ax.set_ylim(0, 1.05); ax.set_xlabel(km["unit"] or "time", fontsize=8); ax.set_ylabel("Proportion maintaining effect", fontsize=8)
        ax.spines[["top", "right"]].set_visible(False); fig.tight_layout(); fig.savefig(out / "figures" / "duration_km.png", dpi=200); plt.close(fig)

    for ag in cfg.get("raters", []):
        cols = ag["cols"]; t = ag.get("type", "ordinal")
        if t == "continuous":
            row = icc21(df[cols].values)
        else:
            if len(cols) != 2: sys.exit("kappa needs exactly 2 rater columns")
            row = cohen_kappa(df[cols[0]], df[cols[1]], weighted=(t == "ordinal")); row["interpretation"] = interpret_kappa(row["kappa"])
        row["label"] = ag["label"]; res["agreement"].append(row)
        md += [f"## Inter-rater agreement: {ag['label']}", "", json.dumps(row, ensure_ascii=False), ""]

    if res["warnings"]:
        md += ["## Warnings", ""] + [f"- {w}" for w in res["warnings"]]
    (out / "results.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "results.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Wrote {out/'results.json'}, {out/'results.md'}, figures in {out/'figures'}")
    for w in res["warnings"]: print("WARNING:", w)


if __name__ == "__main__":
    main()
