#!/usr/bin/env python3
"""Per-test flake log: rerun the UNMUTATED suite at each parent commit N extra times (suite_P is run 1).
Usage: flake_log.py REPO M2DIR OUT.json [--runs 4]. Output {parent: {test_file: [status,...]}}; mixed statuses = flaky at that parent. Resumable."""
import argparse, glob, json, os, pathlib, subprocess, sys, tempfile
H = pathlib.Path(__file__).resolve().parent; R0 = H.parent / "m0_runner" / "run_suite.py"
ap = argparse.ArgumentParser(); ap.add_argument("repo"); ap.add_argument("m2dir"); ap.add_argument("out"); ap.add_argument("--runs", type=int, default=4)
a = ap.parse_args(); out = json.load(open(a.out)) if os.path.exists(a.out) else {}
for f in sorted(glob.glob(a.m2dir + "/[0-9a-f]*.json")):
    r = json.load(open(f)); P = r["parent"]
    if P in out: continue
    runs = [{t: v["status"] for t, v in r["suite_P"]["files"].items()}]
    for i in range(a.runs):
        with tempfile.NamedTemporaryFile(suffix=".json") as tf:
            subprocess.run([sys.executable, str(R0), a.repo, "--commit", P, "--out", tf.name], check=True, capture_output=True)
            runs.append({t: v["status"] for t, v in json.load(open(tf.name))["files"].items()})
    out[P] = {t: [x.get(t) for x in runs] for t in runs[0]}; json.dump(out, open(a.out, "w"))
    print("done", P[:8], [t for t, s in out[P].items() if len(set(s)) > 1], file=sys.stderr)
