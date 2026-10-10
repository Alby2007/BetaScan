#!/usr/bin/env python3
"""trpc_pilot/<C>.json -> rows.jsonl in the h3 mutant_rows schema (mutant, test_file, covers, fails, dur_ms).
Usage: build_rows.py REPO PILOTDIR OUT.jsonl [--worst-case]
Green set: suite_P files marked pass (pass in BOTH suite runs) when the record stores suite_P; otherwise
reconstructed as scoped .test. files at P (git ls-tree over packages/{server,client,tests}) minus excluded_files.
Records without suite_P/cov_P get dur_ms=0 (time_frac metrics degenerate) and no covsize (B5b/B5d/B6 tie-breaks
degrade to coverage-set membership). --worst-case: unresolved mutants included with all covering tests failing."""
import argparse, json, pathlib, subprocess

ap = argparse.ArgumentParser()
ap.add_argument("repo"); ap.add_argument("pilotdir"); ap.add_argument("out")
ap.add_argument("--worst-case", action="store_true")
a = ap.parse_args()
repo = pathlib.Path(a.repo).resolve()
TEST_PKGS = ("packages/server", "packages/client", "packages/tests")
git = lambda *x: subprocess.run(["git", "-C", str(repo), *x], capture_output=True, text=True, encoding="utf-8", errors="replace", check=True).stdout

rows = []; nres = 0
for f in sorted(pathlib.Path(a.pilotdir).glob("[0-9a-f]*.json")):
    d = json.load(open(f)); P = d["parent"]
    if "suite_P" in d:
        sf = d["suite_P"]["files"]
        green = [t for t, v in sf.items() if v["status"] == "pass"]
        dur = {t: v.get("duration_ms", 0) for t, v in sf.items()}
    else:
        excl = set(d.get("excluded_files", []))
        green = [t for t in git("ls-tree", "-r", "--name-only", P, *TEST_PKGS).split() if ".test." in t and t not in excl]
        dur = {}
    gs = set(green)
    for m in d["mutants"]:
        unresolved = m["status"] in ("Error", "Flaky")
        if unresolved and not a.worst_case: continue
        if m["status"] not in ("Killed", "Survived") and not unresolved: continue
        cov = set(m["tests"]); killed = (cov & gs) if unresolved else (set(m["killed_by_files"]) & gs)
        if m["status"] == "Killed" and not killed: continue
        nres += unresolved
        for t in green:
            rows.append({"change_id": f"{P[:10]}:{m['id']}", "kind": "mutant", "parent": P, "date": d["date"],
                         "src_file": m["file"], "mutator": m["mutator"], "line": m["line"], "test_file": t,
                         "covers": int(t in cov), "fails": int(t in killed), "dur_ms": dur.get(t, 0), "unresolved": int(unresolved)})
pathlib.Path(a.out).write_text("\n".join(map(json.dumps, rows)) + "\n")
ch = {r["change_id"] for r in rows}; killed = {r["change_id"] for r in rows if r["fails"]}
print(len(rows), "rows,", len(ch), "mutants,", len(killed), "with a failing test (", nres, "unresolved included); fails+ rows:", sum(r["fails"] for r in rows))
