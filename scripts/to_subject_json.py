#!/usr/bin/env python3
"""Bridge: case.json (this skill) → subject.json for the medical-aesthetics-report PPT skill.

Usage:
  to_subject_json.py case.json --out subjects/<id>/subject.json [--theme clinical]

Only copies fields that exist; never invents values. The PPT skill expects Chinese-style
field names but accepts English values. Review the output before building the deck.
"""
import argparse, json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("case"); ap.add_argument("--out", required=True); ap.add_argument("--theme", default="clinical")
    a = ap.parse_args()
    c = json.loads(Path(a.case).read_text(encoding="utf-8"))
    p = c.get("patient", {}); iv = c.get("interventions", [])
    s = {"id": c.get("case_id", "case1"), "theme": a.theme,
         "cover_title": c.get("working_title", ""),
         "abbr": p.get("initials", ""), "sex": p.get("sex", ""), "age": str(p.get("age", "")),
         "history": p.get("medical_history", ""), "aesthetic_history": "; ".join(
             f"{h.get('treatment','')} {h.get('area','')} ({h.get('when','')})".strip() for h in p.get("aesthetic_history", [])),
         "complaint": c.get("presenting_concern", ""), "diagnosis": c.get("diagnosis", {}).get("final", ""),
         "goals": p.get("goal", ""),
         "plan": "; ".join(x.get("summary", x.get("product", x.get("device", ""))) for x in iv),
         "device": ", ".join(x["device"] for x in iv if x.get("device")),
         "device_param": "; ".join(", ".join(f"{k} {v}" for k, v in x.items() if k in ("wavelength", "fluence", "pulse_width", "spot_size", "passes")) for x in iv if x.get("device")),
         "period": ", ".join(f"Day {e['day']}" for e in c.get("timeline", []) if e.get("kind") == "followup")}
    if c.get("split_face"):
        s["test_side"] = c["split_face"].get("test_side", ""); s["control_side"] = c["split_face"].get("control_side", "")
    charts = []
    for o in c.get("outcomes", []):
        tp = o.get("timepoints", {})
        if tp and all(isinstance(v, (int, float)) for v in tp.values()):
            charts.append({"id": o["measure"].lower().replace(" ", "_"), "type": "line", "title": o["measure"], "unit": o.get("unit", ""),
                           "timepoints": list(tp), "series": [{"name": o.get("side", "value"), "role": o.get("role", "test"), "values": list(tp.values())}]})
    if charts: s["charts"] = charts
    s = {k: v for k, v in s.items() if v not in ("", [], None)}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {a.out} ({len(s)} fields). Review before running medical-aesthetics-report.")


if __name__ == "__main__":
    main()
