#!/usr/bin/env python3
"""Flag potential patient identifiers in a manuscript or case file before it leaves the clinic.

Usage:
  deid_check.py FILE [FILE ...] [--out review/deid.md]

Heuristic only — it flags, a human decides. Checks: calendar dates (use day offsets
such as 'Day 14' instead), phone numbers, e-mails, Chinese resident ID numbers, record /
admission numbers, CJK text inside an English manuscript (often a name or clinic), and
photo filenames that look like real names or IDs. Also reminds about facial photos.
"""
import argparse, re
from pathlib import Path

PATTERNS = [
    ("calendar date", r"\b(19|20)\d{2}[-/.年](0?[1-9]|1[0-2])[-/.月](0?[1-9]|[12]\d|3[01])日?\b"),
    ("calendar date", r"\b(0?[1-9]|[12]\d|3[01])\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(19|20)\d{2}\b"),
    ("calendar date", r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(0?[1-9]|[12]\d|3[01]),?\s+(19|20)\d{2}\b"),
    ("phone number", r"(?<!\d)(\+?86[- ]?)?1[3-9]\d{9}(?!\d)|(?<!\d)0\d{2,3}-\d{7,8}(?!\d)"),
    ("e-mail", r"[\w.+-]+@[\w-]+\.[\w.]+"),
    ("resident ID", r"(?<!\d)\d{17}[\dXx](?!\d)"),
    ("record number", r"(?i)\b(MRN|record\s*(no|number)|admission\s*(no|number)|patient\s*id)\b\s*[:#]?\s*\w+|病历号|住院号|门诊号"),
    ("CJK text (name/clinic?)", r"[一-鿿]{2,}"),
    ("image filename", r"[\w一-鿿-]+\.(jpe?g|png|heic|tiff?)"),
]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("files", nargs="+"); ap.add_argument("--out"); a = ap.parse_args()
    rows = []
    for f in a.files:
        for i, line in enumerate(Path(f).read_text(encoding="utf-8", errors="ignore").split("\n"), 1):
            for label, pat in PATTERNS:
                for m in re.finditer(pat, line):
                    rows.append((Path(f).name, i, label, m.group(0)[:40]))
    rep = ["# De-identification check", "", f"Flags: {len(rows)}", ""]
    if rows:
        rep += ["| file | line | type | text |", "|---|---|---|---|"] + [f"| {f} | {l} | {t} | {x} |" for f, l, t, x in rows]
    rep += ["", "Always also confirm manually:",
            "- Facial photographs: eye bars do NOT de-identify a face. Publish identifiable photos only with written consent specific to publication.",
            "- Replace calendar dates with day offsets from the index treatment (Day 0).",
            "- Remove tattoos, jewellery, birthmarks, background details and EXIF metadata from images.",
            "- Age may be given in years; for very rare presentations consider an age range."]
    out = "\n".join(rep) + "\n"
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True); Path(a.out).write_text(out, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
