#!/usr/bin/env python3
"""Sample real commits and, for each (parent P, commit C), record suite results at P and C and per-test coverage at P.
Usage: harvest_commits.py REPO OUTDIR --n 12 [--seed 0] [--since 2025-01-01]
Output: OUTDIR/<C>.json = {commit, parent, files_changed:[...], suite_P, suite_C, cov_P}. Resumable."""
import argparse, json, pathlib, random, subprocess, sys
H = pathlib.Path(__file__).resolve().parent; R0 = H.parent / "m0_runner" / "run_suite.py"
ap = argparse.ArgumentParser(); ap.add_argument("repo"); ap.add_argument("outdir")
ap.add_argument("--n", type=int, default=12); ap.add_argument("--seed", type=int, default=0); ap.add_argument("--since", default="2025-01-01"); ap.add_argument("--skip-c", action="store_true", help="skip the suite run at C (mutant-only use)"); ap.add_argument("--exclude-dir", default="")
a = ap.parse_args(); out = pathlib.Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
git = lambda *x: subprocess.run(["git", "-C", a.repo, *x], capture_output=True, text=True, check=True).stdout
cands = []
for c in git("rev-list", "--no-merges", f"--since={a.since}", "HEAD").split():
    fs = git("diff-tree", "--no-commit-id", "--name-only", "-r", c).split()
    if any(f.startswith("src/") and f.endswith(".ts") for f in fs) and git("rev-list", "--parents", "-n1", c).split()[1:]: cands.append(c)
random.Random(a.seed).shuffle(cands); print(len(cands), "candidates", file=sys.stderr)
done = 0
for c in cands:
    if done >= a.n: break
    f = out / f"{c}.json"
    if a.exclude_dir and (pathlib.Path(a.exclude_dir) / f"{c}.json").exists(): continue
    if f.exists(): done += 1; continue
    p = git("rev-parse", f"{c}^").strip()
    try:
        run = lambda sha, o: subprocess.run([sys.executable, str(R0), a.repo, "--commit", sha, "--out", o], check=True, capture_output=True)
        run(p, str(out / "_p.json"))
        if not a.skip_c: run(c, str(out / "_c.json"))
        subprocess.run([sys.executable, str(H / "coverage_per_test.py"), a.repo, p, str(out / "_cov.json")], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print("skip", c, "install/run failed", file=sys.stderr); (out / f"{c}.skip").write_text(e.stderr.decode()[-2000:] if e.stderr else ""); continue
    rec = {"commit": c, "parent": p, "files_changed": git("diff-tree", "--no-commit-id", "--name-only", "-r", c).split(),
           "diff": git("diff", "-U0", p, c, "--", "src"), "date": git("log", "-1", "--format=%cI", c).strip(),
           "suite_P": json.load(open(out / "_p.json")), "suite_C": {"files": {}} if a.skip_c else json.load(open(out / "_c.json")), "cov_P": json.load(open(out / "_cov.json"))}
    f.write_text(json.dumps(rec)); done += 1; print("done", c, done, file=sys.stderr)
