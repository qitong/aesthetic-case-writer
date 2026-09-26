#!/usr/bin/env python3
"""Draw the CARE timeline figure from case.json.

Usage:
  timeline_figure.py case.json --out figures/timeline.png [--unit days|weeks|months]

Reads case.json["timeline"]: [{"day": 0, "label": "...", "kind": "treatment|event|management|followup"}, ...]
Day 0 = index treatment. Labels should be short (≤ 40 characters); details belong in the text.
"""
import argparse, json, textwrap
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

COL = {"treatment": "#0C7A5C", "event": "#C0392B", "management": "#D4A017", "followup": "#6A847C"}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("case"); ap.add_argument("--out", default="figures/timeline.png")
    ap.add_argument("--unit", choices=["days", "weeks", "months"], default="days"); a = ap.parse_args()
    tl = sorted(json.loads(Path(a.case).read_text(encoding="utf-8"))["timeline"], key=lambda e: e["day"])
    div = {"days": 1, "weeks": 7, "months": 30.44}[a.unit]
    xs = [e["day"] / div for e in tl]
    fig, ax = plt.subplots(figsize=(10, 3.2))
    ax.axhline(0, color="#333", lw=1.2, zorder=1)
    for i, (x, e) in enumerate(zip(xs, tl)):
        up = 1 if i % 2 == 0 else -1; c = COL.get(e.get("kind", "followup"), "#333")
        ax.scatter([x], [0], s=60, color=c, zorder=3)
        ax.plot([x, x], [0, 0.55 * up], color=c, lw=1, zorder=2)
        lab = f"{'Day' if a.unit == 'days' else a.unit[:-1].title()} {x:g}\n" + "\n".join(textwrap.wrap(e["label"], 22))
        ax.text(x, 0.62 * up, lab, ha="center", va="bottom" if up > 0 else "top", fontsize=8, color="#222")
    pad = (max(xs) - min(xs)) * 0.08 or 1
    ax.set_xlim(min(xs) - pad, max(xs) + pad); ax.set_ylim(-2, 2); ax.axis("off")
    handles = [plt.Line2D([], [], marker="o", ls="", color=v, label=k) for k, v in COL.items() if any(e.get("kind") == k for e in tl)]
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.12), ncol=len(handles), frameon=False, fontsize=8)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(); fig.savefig(a.out, dpi=250); print(f"Wrote {a.out}")


if __name__ == "__main__":
    main()
