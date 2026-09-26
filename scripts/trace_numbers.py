#!/usr/bin/env python3
"""Audit that every number in the manuscript can be traced to a source file.

Usage:
  trace_numbers.py MANUSCRIPT.md --sources case.json analysis/results.json notes.md ... [--out review/trace.md]

Every numeric token in the manuscript body (References section excluded, citation
brackets like [3] or [1–4] excluded) is looked up in the numbers found in the sources.
Matching tolerates rounding (12.46 in a source matches 12.5 in the text) and
percent/fraction forms (0.45 ↔ 45). Anything unmatched is listed for the author to
confirm or correct — unmatched does not always mean wrong (e.g., derived sums), but
each must be explained.
"""
import argparse, json, re
from pathlib import Path

NUM = re.compile(r"(?<![\w.])[-−–]?\d{1,3}(?:,\d{3})+(?:\.\d+)?|(?<![\w.])[-−–]?\d+(?:\.\d+)?")
CITE = re.compile(r"\[\s*\d+(?:\s*[,–-]\s*\d+)*\s*\]|\^\d+(?:[,–-]\d+)*\^")


def numbers(text):
    out = []
    for m in NUM.finditer(text):
        tok = m.group(0).replace(",", "").replace("−", "-").replace("–", "-")
        try:
            out.append((float(tok), m.group(0), m.start()))
        except ValueError:
            pass
    return out


def source_numbers(paths):
    vals = set()
    for p in paths:
        t = Path(p).read_text(encoding="utf-8", errors="ignore")
        if p.endswith(".json"):
            def walk(o):
                if isinstance(o, bool): return
                if isinstance(o, (int, float)): vals.add(float(o))
                elif isinstance(o, dict): [walk(v) for v in o.values()] ; [vals.update(v for v, _, _ in numbers(k)) for k in o]
                elif isinstance(o, list): [walk(v) for v in o]
                elif isinstance(o, str): vals.update(v for v, _, _ in numbers(o))
            walk(json.loads(t))
        else:
            vals.update(v for v, _, _ in numbers(t))
    return vals


def matches(x, pool):
    dec = 0
    for v in pool:
        for cand in (v, v * 100, v / 100, abs(v)):
            for d in range(0, 4):
                if round(cand, d) == x or abs(cand - x) < 1e-9:
                    return True
    return False


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("manuscript"); ap.add_argument("--sources", nargs="+", required=True); ap.add_argument("--out")
    a = ap.parse_args()
    text = Path(a.manuscript).read_text(encoding="utf-8")
    body = re.split(r"\n#+\s*References\b", text, flags=re.I)[0]
    body = CITE.sub(" ", body)
    pool = source_numbers(a.sources)
    lines = body.split("\n"); pos = []; acc = 0
    for i, ln in enumerate(lines):
        pos.append(acc); acc += len(ln) + 1
    unmatched, n = [], 0
    for x, raw, start in numbers(body):
        n += 1
        if 1900 <= x <= 2100 and float(x).is_integer():  # years
            continue
        if not matches(x, pool):
            ln = max(i for i, p in enumerate(pos) if p <= start)
            unmatched.append((raw, ln + 1, lines[ln].strip()[:120]))
    rep = [f"# Number traceability audit", "", f"Numbers checked: {n}; unmatched: {len(unmatched)}", ""]
    if unmatched:
        rep += ["| number | line | context |", "|---|---|---|"] + [f"| {r} | {l} | {c.replace('|', '/')} |" for r, l, c in unmatched]
        rep += ["", "Each unmatched number must be (a) corrected, (b) traced to a source added to --sources, or (c) explained (e.g., derived: 'sum of two sessions')."]
    else:
        rep.append("All numbers trace to the sources.")
    out = "\n".join(rep) + "\n"
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True); Path(a.out).write_text(out, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
