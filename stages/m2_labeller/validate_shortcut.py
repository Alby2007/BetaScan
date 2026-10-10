#!/usr/bin/env python3
"""Check the 'only run covering tests' shortcut: for sampled mutants run the NON-covering green tests too and count failures.
Usage: validate_shortcut.py REPO M2DIR MUTDIR OUT.json [--parents 3] [--per-parent 8] [--seed 0]"""
import argparse, json, pathlib, random, subprocess, sys, tempfile
H = pathlib.Path(__file__).resolve().parent
ap = argparse.ArgumentParser(); ap.add_argument("repo"); ap.add_argument("m2dir"); ap.add_argument("mutdir"); ap.add_argument("out")
ap.add_argument("--parents", type=int, default=3); ap.add_argument("--per-parent", type=int, default=8); ap.add_argument("--seed", type=int, default=0); ap.add_argument("--risky", default="", help="graphs.db: pick high-risk mutants (hub files, module top-level code) instead of random; --per-parent-random extra random ones"); ap.add_argument("--per-parent-random", type=int, default=0)
a = ap.parse_args(); repo = pathlib.Path(a.repo).resolve(); rng = random.Random(a.seed)
files = sorted(pathlib.Path(a.mutdir).glob("*.json")); rng.shuffle(files); report = []
import sqlite3
con = sqlite3.connect(a.risky) if a.risky else None
gen = lambda wt, fs: json.loads(subprocess.run(["node", str(H / "gen_mutants.mjs"), wt, *fs], capture_output=True, text=True, check=True).stdout)
for f in files[: a.parents]:
    d = json.load(open(f)); rec = json.load(open(pathlib.Path(a.m2dir) / f"{d['commit']}.json")); P = d["parent"]
    green = [t for t, v in rec["suite_P"]["files"].items() if v["status"] == "pass"]
    ms = [m for m in d["mutants"] if m["status"] in ("Killed", "Survived")]; rng.shuffle(ms)
    if con:
        def risk(m):
            imp = con.execute("""WITH RECURSIVE up(id) AS (SELECT ? UNION SELECT e.src FROM edges e JOIN up ON e.dst=up.id WHERE e.type='imports' AND e.commit_hash=?) SELECT count(*) FROM up""", (f"file:{m['file']}", P)).fetchone()[0]
            fn = con.execute("SELECT count(*) FROM nodes WHERE commit_hash=? AND kind='function' AND file=? AND start_line<=? AND end_line>=?", (P, m["file"], m["line"], m["line"])).fetchone()[0]
            return (fn == 0, imp)
        ranked = sorted(ms, key=risk, reverse=True); pick = ranked[: a.per_parent]
        ms = pick + [m for m in ranked[a.per_parent:] if True][: 0] + rng.sample([m for m in ranked[a.per_parent:]], min(a.per_parent_random, len(ranked) - a.per_parent))
        for m in ms: m["_risk"] = risk(m)
    else: ms = ms[: a.per_parent]
    with tempfile.TemporaryDirectory() as wt:
        subprocess.run(f"git -C {repo} archive {P} src | tar -x -C {wt}", shell=True, check=True)
        allm = {f"{m['file']}:{m['start']}:{m['mutator']}": m for m in gen(wt, sorted({m['file'] for m in ms}))}
    jobs = [{"id": m["id"], "file": m["file"], "start": allm[m["id"]]["start"], "end": allm[m["id"]]["end"], "replacement": m["replacement"],
             "tests": [t for t in green if t not in set(m["tests"])]} for m in ms]
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp); (tmp / "out").mkdir()
        subprocess.run(["git", "-C", str(repo), "archive", "-o", str(tmp / "src.tar"), P], check=True)
        (tmp / "jobs.json").write_text(json.dumps(jobs)); (tmp / "run_mutants.mjs").write_text((H / "run_mutants.mjs").read_text())
        script = "tar -xf /in/src.tar -C /repo && cd /repo && pnpm install --frozen-lockfile >&2 && node /in/run_mutants.mjs /in/jobs.json /out/res.json"
        subprocess.run(["docker", "run", "--rm", "-v", f"{tmp}:/in", "-v", f"{tmp}/out:/out", "-v", "impactnet-pnpm-store:/root/.local/share/pnpm", "-e", "CI=true", "-e", "BASELINE=1", "impactnet-node", "bash", "-c", script], capture_output=True)
        res = json.loads((tmp / "out/res.json").read_text())
    for j, r in zip(jobs, res): report.append({"parent": P, "id": j["id"], "risk": ms[[m["id"] for m in ms].index(j["id"])].get("_risk"), "n_noncovering": len(j["tests"]), "status": r["status"], "extra_failures": r["killed_by_files"]})
    print("parent", P[:8], "done", file=sys.stderr)
pathlib.Path(a.out).write_text(json.dumps(report, indent=1))
bad = [r for r in report if r["extra_failures"]]
print(len(report), "mutants checked;", len(bad), "had a failing non-covering test;", sum(len(r["extra_failures"]) for r in bad), "extra failures")
