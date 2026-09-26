#!/usr/bin/env python3
"""State manager for the interactive CARE / PROCESS self-review.

Claude does the semantic work (reading the manuscript, asking the user, revising text);
this script only keeps a durable record of each item's status so the review can be
resumed and exported as a submission-ready checklist.

Usage:
  checklist_session.py init    --type care|process --out review/checklist_state.json
  checklist_session.py status  STATE [--pending] [--json]
  checklist_session.py next    STATE [--n 3]          # next unresolved items, grouped by section
  checklist_session.py set     STATE ID --status STATUS [--location TEXT] [--note TEXT]
  checklist_session.py export  STATE --md OUT.md [--docx OUT.docx]

Statuses:
  pending       not yet checked
  reported      already in the manuscript (location required)
  added         missing, user supplied info, manuscript revised (location required)
  not_available user confirmed the information does not exist (note required)
  na            not applicable to this case (note required)
"""
import argparse, json, subprocess, sys
from datetime import datetime
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets" / "checklists"
FILES = {"care": "care_aesthetic.json", "process": "process_aesthetic.json"}
STATUSES = ["pending", "reported", "added", "not_available", "na"]
DONE = {"reported", "added", "not_available", "na"}


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def save(p, data):
    data["updated"] = datetime.now().isoformat(timespec="seconds")
    Path(p).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def cmd_init(a):
    src = load(ASSETS / FILES[a.type])
    out = Path(a.out)
    if out.exists() and not a.force:
        sys.exit(f"{out} exists; use --force to overwrite (this discards recorded answers).")
    out.parent.mkdir(parents=True, exist_ok=True)
    state = {"checklist": src["name"], "type": a.type, "source_note": src["source_note"],
             "created": datetime.now().isoformat(timespec="seconds"),
             "items": [dict(it, status="pending", location="", note="") for it in src["items"]]}
    if "appraisal" in src:
        state["appraisal"] = {"name": src["appraisal"]["name"],
                              "items": [{"q": q, "answer": "", "note": ""} for q in src["appraisal"]["items"]]}
    save(out, state)
    print(f"Initialised {len(state['items'])} items → {out}")


def summary(state):
    c = {s: 0 for s in STATUSES}
    for it in state["items"]:
        c[it["status"]] += 1
    crit_open = [it["id"] for it in state["items"]
                 if it.get("critical") and it["status"] in ("pending", "not_available")]
    return c, crit_open


def cmd_status(a):
    st = load(a.state)
    c, crit = summary(st)
    if a.json:
        print(json.dumps({"counts": c, "critical_open": crit}, ensure_ascii=False)); return
    print(f"{st['checklist']}\n" + "  ".join(f"{k}={v}" for k, v in c.items()))
    if crit:
        print("Critical items still open or unavailable: " + ", ".join(crit))
    for it in st["items"]:
        if a.pending and it["status"] in DONE:
            continue
        flag = "!" if it.get("critical") else " "
        loc = f" @ {it['location']}" if it["location"] else ""
        print(f"{flag}[{it['status']:<13}] {it['id']:<4} {it['section']}: {it['item'][:70]}{loc}")


def cmd_next(a):
    st = load(a.state)
    pend = [it for it in st["items"] if it["status"] == "pending"]
    if not pend:
        print("No pending items."); return
    sec = pend[0]["section"].split(" · ")[0]
    batch = [it for it in pend if it["section"].split(" · ")[0] == sec][: a.n]
    for it in batch:
        print(f"## {it['id']} — {it['section']}{'  [CRITICAL]' if it.get('critical') else ''}")
        print(f"Requirement: {it['item']}")
        for x in it.get("aesthetic", []):
            print(f"  + aesthetic: {x}")
        print(f"Suggested question: {it['ask'] or '(no question — check the manuscript text yourself)'}\n")


def cmd_set(a):
    st = load(a.state)
    if a.status not in STATUSES:
        sys.exit(f"status must be one of {STATUSES}")
    if a.status in ("reported", "added") and not a.location:
        sys.exit("--location is required for reported/added (section + paragraph, e.g. 'Case presentation ¶2').")
    if a.status in ("not_available", "na") and not a.note:
        sys.exit("--note is required for not_available/na (say why).")
    for it in st["items"]:
        if it["id"] == a.id:
            it["status"], it["location"], it["note"] = a.status, a.location or "", a.note or ""
            save(a.state, st); print(f"{a.id} → {a.status}"); return
    sys.exit(f"Unknown item id {a.id}")


def cmd_appraise(a):
    st = load(a.state)
    if "appraisal" not in st:
        sys.exit("This checklist has no appraisal section.")
    it = st["appraisal"]["items"][a.index - 1]
    it["answer"], it["note"] = a.answer, a.note or ""
    save(a.state, st); print(f"Appraisal {a.index} → {a.answer}")


def cmd_export(a):
    st = load(a.state)
    c, crit = summary(st)
    label = {"reported": "Reported", "added": "Reported (added in review)",
             "not_available": "Not reported — information unavailable", "na": "Not applicable", "pending": "NOT CHECKED"}
    L = [f"# {st['checklist']}", "", f"_{st['source_note']}_", "",
         "| Item | Section | Requirement | Reported at | Status / note |", "|---|---|---|---|---|"]
    for it in st["items"]:
        note = label[it["status"]] + (f" — {it['note']}" if it["note"] else "")
        req = it["item"].replace("|", "/")
        L.append(f"| {it['id']} | {it['section']} | {req} | {it['location'] or '—'} | {note} |")
    if st.get("appraisal"):
        L += ["", f"## {st['appraisal']['name']}", "", "| # | Question | Answer | Note |", "|---|---|---|---|"]
        for i, q in enumerate(st["appraisal"]["items"], 1):
            L.append(f"| {i} | {q['q']} | {q['answer'] or '—'} | {q['note']} |")
    L += ["", f"Summary: " + ", ".join(f"{k}={v}" for k, v in c.items())]
    if crit:
        L.append(f"**Open critical items: {', '.join(crit)}**")
    Path(a.md).write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"Wrote {a.md}")
    if a.docx:
        subprocess.run(["pandoc", a.md, "-o", a.docx], check=True); print(f"Wrote {a.docx}")


def main():
    p = argparse.ArgumentParser(); s = p.add_subparsers(dest="cmd", required=True)
    x = s.add_parser("init"); x.add_argument("--type", choices=list(FILES), required=True); x.add_argument("--out", required=True); x.add_argument("--force", action="store_true"); x.set_defaults(f=cmd_init)
    x = s.add_parser("status"); x.add_argument("state"); x.add_argument("--pending", action="store_true"); x.add_argument("--json", action="store_true"); x.set_defaults(f=cmd_status)
    x = s.add_parser("next"); x.add_argument("state"); x.add_argument("--n", type=int, default=3); x.set_defaults(f=cmd_next)
    x = s.add_parser("set"); x.add_argument("state"); x.add_argument("id"); x.add_argument("--status", required=True); x.add_argument("--location"); x.add_argument("--note"); x.set_defaults(f=cmd_set)
    x = s.add_parser("appraise"); x.add_argument("state"); x.add_argument("index", type=int); x.add_argument("--answer", choices=["yes", "no", "unclear", "na"], required=True); x.add_argument("--note"); x.set_defaults(f=cmd_appraise)
    x = s.add_parser("export"); x.add_argument("state"); x.add_argument("--md", required=True); x.add_argument("--docx"); x.set_defaults(f=cmd_export)
    a = p.parse_args(); a.f(a)


if __name__ == "__main__":
    main()
