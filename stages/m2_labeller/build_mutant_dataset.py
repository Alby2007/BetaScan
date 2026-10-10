#!/usr/bin/env python3
"""build_mutant_dataset.py OUT.jsonl --pair M2DIR:MUTDIR [--pair ...] [--flake FLAKE.json ...] [--worst-case]
Rows (mutant, test_file, covers, fails). Kill rule: a test counts as killing only if it passed in ALL clean runs of the flake logs AND failed in both mutant runs.
--worst-case: mutants with no resolved outcome (Error/Flaky) are INCLUDED as kills in which every covering test fails (failing fraction 1, the worst case for headroom)."""
import argparse, json, pathlib
ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--pair", action="append", required=True); ap.add_argument("--flake", action="append", default=[]); ap.add_argument("--worst-case", action="store_true")
a = ap.parse_args(); flake = {}
for f in a.flake: flake.update(json.load(open(f)))
clean = lambda P, t: not flake or set(flake.get(P, {}).get(t, ["x"])) == {"pass"}
rows = []; nres = 0
for pr in a.pair:
    m2, mut = map(pathlib.Path, pr.split(":"))
    for f in sorted(mut.glob("*.json")):
        d = json.load(open(f)); rec = json.load(open(m2 / f"{d['commit']}.json"))
        green = [t for t, v in rec["suite_P"]["files"].items() if v["status"] == "pass" and clean(d["parent"], t)]
        for m in d["mutants"]:
            unresolved = m["status"] in ("Error", "Flaky")
            if unresolved and not a.worst_case: continue
            if m["status"] not in ("Killed", "Survived") and not unresolved: continue
            cov = set(m["tests"]); killed = (cov & set(green)) if unresolved else {t for t in m["killed_by_files"] if clean(d["parent"], t)}
            if m["status"] == "Killed" and not killed: continue
            nres += unresolved
            for t in green:
                rows.append({"change_id": f"{d['parent'][:10]}:{m['id']}", "kind": "mutant", "parent": d["parent"], "date": d["date"], "src_file": m["file"], "mutator": m["mutator"],
                             "line": m["line"], "test_file": t, "covers": int(t in cov), "fails": int(t in killed), "dur_ms": rec["suite_P"]["files"][t]["duration_ms"], "unresolved": int(unresolved)})
pathlib.Path(a.out).write_text("\n".join(map(json.dumps, rows)) + "\n")
ch = {r["change_id"] for r in rows}; killed = {r["change_id"] for r in rows if r["fails"]}
print(len(rows), "rows,", len(ch), "mutants,", len(killed), "with a failing test (", nres, "unresolved included); fails+ rows:", sum(r["fails"] for r in rows))
