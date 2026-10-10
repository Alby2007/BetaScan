#!/usr/bin/env python3
"""build_dataset.py M2DIR out.jsonl -> rows (commit, test_file, covers, fails, ...) one per (change, test file).
covers: test covers >=1 changed line (old-side coordinates, parent commit coverage).
fails : test passes at P and fails at C. Tests not passing at P are excluded (cannot be labelled)."""
import json, pathlib, re, sys
d, out = pathlib.Path(sys.argv[1]), sys.argv[2]
rows = []
for f in sorted(d.glob("[0-9a-f]*.json")):
    r = json.load(open(f)); cov = r["cov_P"]["tests"]
    changed, cur = {}, None
    for l in r["diff"].splitlines():
        if l.startswith("--- a/"): cur = l[6:]
        elif l.startswith("--- "): cur = None
        m = re.match(r"@@ -(\d+)(?:,(\d+))? \+", l)
        if m and cur:
            s, n = int(m[1]), int(m[2]) if m[2] is not None else 1
            changed.setdefault(cur, set()).update(range(s, s + n) if n else {s, s + 1})
    for t, p in r["suite_P"]["files"].items():
        if p["status"] != "pass": continue
        c = r["suite_C"]["files"].get(t, {}).get("status")
        cv = cov.get(t, {}).get("covered", {})
        covers = any(set(ls) & set(cv.get(fn, [])) for fn, ls in changed.items())
        rows.append({"commit": r["commit"], "parent": r["parent"], "date": r["date"], "test_file": t, "covers": int(covers),
                     "fails": int(c == "fail"), "dur_ms": p["duration_ms"], "src_files_changed": sorted(changed)})
open(out, "w").write("\n".join(json.dumps(x) for x in rows) + "\n")
n = len({x["commit"] for x in rows}); print(len(rows), "rows,", n, "commits, covers+:", sum(x["covers"] for x in rows), "fails+:", sum(x["fails"] for x in rows))
