#!/usr/bin/env python3
"""Real-commit stratum report (kept separate from mutants). Usage: real_commit_strata.py M2DIR
Per real commit: does line coverage at P apply (B5 defined) and are there any `fails` labels (full-suite runs, no shortcut)?"""
import glob, json, sys
print("| commit | date | src files | config/fixture/other files | tests (green@P) | covering tests | tests failing at C (pass@P) | B5 defined |\n|---|---|---|---|---|---|---|---|")
tot = {"b5": 0, "undef": 0, "fails": 0}
for f in sorted(glob.glob(sys.argv[1] + "/[0-9a-f]*.json"), key=lambda p: json.load(open(p))["date"]):
    r = json.load(open(f)); fc = r["files_changed"]; src = [x for x in fc if x.startswith("src/") and x.endswith(".ts")]; non = [x for x in fc if x not in src and not (x.startswith("docs/") or x.endswith(".md") or x.startswith("test/") or x.startswith("examples/") or x.startswith("playground/"))]
    green = [t for t, v in r["suite_P"]["files"].items() if v["status"] == "pass"]
    changed = {}
    import re
    cur = None
    for l in r["diff"].splitlines():
        if l.startswith("--- a/"): cur = l[6:]
        m = re.match(r"@@ -(\d+)(?:,(\d+))? \+", l)
        if m and cur: s, n = int(m[1]), int(m[2]) if m[2] is not None else 1; changed.setdefault(cur, set()).update(range(s, s + n) if n else {s, s + 1})
    ncov = sum(1 for t in green if any(set(ls) & set(r["cov_P"]["tests"].get(t, {}).get("covered", {}).get(fn, [])) for fn, ls in changed.items()))
    nf = sum(1 for t in green if r["suite_C"]["files"].get(t, {}).get("status") == "fail")
    b5 = ncov > 0 and not non; tot["b5" if b5 else "undef"] += 1; tot["fails"] += nf
    print(f"| {r['commit'][:8]} | {r['date'][:10]} | {len(src)} | {len(non)} {non[:2] if non else ""} | {len(green)} | {ncov} | {nf} | {'yes' if b5 else 'NO'} |")
print(f"\nB5 defined: {tot['b5']}, undefined (no covering tests, or config/build/other files touched; docs, tests, examples ignored): {tot['undef']}; total real-commit failing-test labels: {tot['fails']}")
