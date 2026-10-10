#!/usr/bin/env python3
"""Mutation labels at parent commits already harvested by harvest_commits.py.
Usage: mutate_commits.py REPO M2DIR OUTDIR [--files-per-commit 4] [--per-file 8] [--seed 0] [--limit N]
For each M2DIR/<C>.json: pick src files covered at P, sample covered-line mutants, run each against only the tests that cover its line,
record killed_by_files. Output OUTDIR/<P>.json (resumable)."""
import argparse, json, pathlib, random, subprocess, sys, tarfile, tempfile
H = pathlib.Path(__file__).resolve().parent
ap = argparse.ArgumentParser(); ap.add_argument("repo"); ap.add_argument("m2dir"); ap.add_argument("outdir")
ap.add_argument("--files-per-commit", type=int, default=4); ap.add_argument("--per-file", type=int, default=8)
ap.add_argument("--seed", type=int, default=0); ap.add_argument("--min-cov", type=int, default=0, help="only mutants on lines covered by >= this many green tests (oversample large covering sets)"); ap.add_argument("--per-commit", type=int, default=0, help="total mutants per commit (with --min-cov)"); ap.add_argument("--limit", type=int, default=999); ap.add_argument("--image", default="impactnet-node")
a = ap.parse_args(); repo = pathlib.Path(a.repo).resolve(); out = pathlib.Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
for rf in sorted(pathlib.Path(a.m2dir).glob("[0-9a-f]*.json"))[: a.limit]:
    r = json.load(open(rf)); P = r["parent"]; o = out / f"{P}.json"
    if o.exists(): continue
    cov = {t: v["covered"] for t, v in r["cov_P"]["tests"].items()}
    green = {t for t, v in r["suite_P"]["files"].items() if v["status"] == "pass"}
    files = sorted({f for c in cov.values() for f in c if f.startswith("src/") and f.endswith(".ts")})
    if a.min_cov:
        cnt = {}
        for t in green:
            for f_, ls in cov.get(t, {}).items():
                for l in ls: cnt[(f_, l)] = cnt.get((f_, l), 0) + 1
        files = [f_ for f_ in files if any(n >= a.min_cov for (ff, _), n in cnt.items() if ff == f_)]
    rng = random.Random(f"{a.seed}{P}"); rng.shuffle(files); files = files[: a.files_per_commit]
    with tempfile.TemporaryDirectory() as wt:
        tar = pathlib.Path(wt) / "src.tar"
        subprocess.run(["git", "-C", str(repo), "archive", "-o", str(tar), P, "src"], check=True)
        with tarfile.open(tar) as tf:
            tf.extractall(wt, filter="data", members=[m for m in tf.getmembers() if not (m.issym() or m.islnk())])
        ms = json.loads(subprocess.run(["node", str(H / "gen_mutants.mjs"), wt, *files], capture_output=True, text=True, encoding="utf-8", errors="replace", check=True).stdout)
    jobs, meta = [], []
    if a.min_cov:
        for mm in ms: mm["tests"] = sorted(t for t in green if mm["line"] in set(cov.get(t, {}).get(mm["file"], []))); 
        pool = [mm for mm in ms if len(mm["tests"]) >= a.min_cov]; rng.shuffle(pool)
        for mm in pool[: a.per_commit]:
            mm["id"] = f"{mm['file']}:{mm['start']}:{mm['mutator']}"; jobs.append({k: mm[k] for k in ("id", "file", "start", "end", "replacement", "tests")}); meta.append(mm)
    for f in ([] if a.min_cov else files):
        fm = [m for m in ms if m["file"] == f]
        for m in fm: m["tests"] = sorted(t for t in green if m["line"] in set(cov.get(t, {}).get(f, [])))
        pool = [m for m in fm if m["tests"]]; rng.shuffle(pool)
        for m in pool[: a.per_file]:
            m["id"] = f"{f}:{m['start']}:{m['mutator']}"; jobs.append({k: m[k] for k in ("id", "file", "start", "end", "replacement", "tests")}); meta.append(m)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp); (tmp / "out").mkdir()
        subprocess.run(["git", "-C", str(repo), "archive", "-o", str(tmp / "src.tar"), P], check=True)
        (tmp / "jobs.json").write_text(json.dumps(jobs)); (tmp / "run_mutants.mjs").write_text((H / "run_mutants.mjs").read_text())
        script = "tar -xf /in/src.tar -C /repo && cd /repo && pnpm install --frozen-lockfile >&2 && node /in/run_mutants.mjs /in/jobs.json /out/res.json"
        p = subprocess.run(["docker", "run", "--rm", "-v", f"{tmp}:/in", "-v", f"{tmp}/out:/out", "-v", "impactnet-pnpm-store:/root/.local/share/pnpm", "-e", "CI=true", a.image, "bash", "-c", script], capture_output=True, text=True, encoding="utf-8", errors="replace")
        resf = tmp / "out/res.json"
        if not resf.exists(): print("fail", P, p.stderr[-500:], file=sys.stderr); continue
        res = {x["id"]: x for x in json.loads(resf.read_text())}
    rows = [{**{k: m[k] for k in ("id", "file", "mutator", "line", "original", "replacement", "tests")}, **{k: res[m["id"]][k] for k in ("status", "killed_by_files", "secs")}} for m in meta if m["id"] in res]
    o.write_text(json.dumps({"parent": P, "commit": r["commit"], "date": r["date"], "mutants": rows}))
    import collections; print("done", P[:8], len(rows), dict(collections.Counter(x["status"] for x in rows)), file=sys.stderr)
