#!/usr/bin/env python3
"""trpc pilot: N commits end-to-end (suite x2, per-test coverage, mutation) restricted to
packages/{server,client,tests}; mutation targets packages/{server,client}/src only.
Same mutation operators as h3 (gen_mutants.mjs, unchanged). Output: OUTDIR/<C>.json per commit (resumable)
plus OUTDIR/summary.json. Usage: pilot.py REPO OUTDIR [--n 3] [--since 2025-09-01] [--min-cov 11] [--per-commit 8] [--files-per-commit 6]"""
import argparse, collections, json, pathlib, random, subprocess, sys, tarfile, tempfile, time

H = pathlib.Path(__file__).resolve().parent
M2 = H.parent
TEST_PKGS = ["packages/server", "packages/client", "packages/tests"]
SRC_PREFIXES = ("packages/server/src/", "packages/client/src/")

ap = argparse.ArgumentParser()
ap.add_argument("repo"); ap.add_argument("outdir")
ap.add_argument("--n", type=int, default=3); ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--since", default="2025-09-01")
ap.add_argument("--min-cov", type=int, default=11); ap.add_argument("--per-commit", type=int, default=25)
ap.add_argument("--augment", type=int, default=0, help="append up to N mutants on not-yet-mutated files to each existing record (needs cov_P/suite_P; skips suite/coverage stages)")
a = ap.parse_args()
repo = pathlib.Path(a.repo).resolve(); out = pathlib.Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
git = lambda *x: subprocess.run(["git", "-C", str(repo), *x], capture_output=True, text=True, encoding="utf-8", errors="replace", check=True).stdout
INSTALL = "COREPACK_ENABLE_STRICT=0 pnpm install --frozen-lockfile"
IMAGE = {"22": "impactnet-node22", "24": "impactnet-node"}
_cur_image = "impactnet-node"

def image_for(sha):
    pkg = json.loads(git("show", f"{sha}:package.json"))
    return IMAGE["22" if "22" in pkg.get("engines", {}).get("node", "24") else "24"]

def docker(script, tmp, extra_env=None, timeout=None):
    env = []
    for k, v in (extra_env or {}).items(): env += ["-e", f"{k}={v}"]
    return subprocess.run(["docker", "run", "--rm", "-v", f"{tmp}:/in", "-v", f"{tmp}/out:/out",
                           "-v", "impactnet-pnpm-store:/root/.local/share/pnpm", "-v", "impactnet-root-cache:/root/.cache",
                           "-e", "CI=true", *env, _cur_image, "bash", "-c", script], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)

COMBINED = r'''
set -u
tar -xf /in/src.tar -C /repo && cd /repo && COREPACK_ENABLE_STRICT=0 pnpm install --frozen-lockfile >&2
s=$(date +%s)
pnpm exec vitest run --reporter=json --outputFile=/tmp/s1.json $TEST_PKGS_ENV >/dev/null 2>&1
cp /tmp/s1.json /out/suite1.json
echo "suite1 $(( $(date +%s)-s ))" >> /out/_times.txt
for f in $(echo $FILES_ENV | tr ',' ' '); do
  rm -rf coverage
  s=$(date +%s)
  timeout 240 pnpm exec vitest --run --coverage --coverage.reporter=json --coverage.all=false "$f" >/tmp/log 2>&1; rc=$?
  n=$(echo "$f" | tr '/' '_')
  [ -f coverage/coverage-final.json ] && cp coverage/coverage-final.json /out/$n.json
  echo "$f $rc $(( $(date +%s)-s ))" >> /out/_index.txt
done
s=$(date +%s)
pnpm exec vitest run --reporter=json --outputFile=/tmp/s2.json $TEST_PKGS_ENV >/dev/null 2>&1
cp /tmp/s2.json /out/suite2.json
echo "suite2 $(( $(date +%s)-s ))" >> /out/_times.txt
'''

def suite_and_cov(sha, all_files):
    """One container: install once, suite run 1, per-file coverage of all_files, suite run 2."""
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td); (tmp / "out").mkdir()
        subprocess.run(["git", "-C", str(repo), "archive", "-o", str(tmp / "src.tar"), sha], check=True)
        t0 = time.time()
        p = docker(COMBINED, tmp, {"FILES_ENV": ",".join(all_files), "TEST_PKGS_ENV": " ".join(TEST_PKGS)})
        if p.returncode: raise RuntimeError("combined container failed: " + p.stderr[-1500:])
        def sres(name):
            raw = json.loads((tmp / "out" / name).read_text())
            files = {}
            for f in raw["testResults"]:
                n = f["name"].removeprefix("/repo/")
                st = {"passed": "pass", "failed": "fail"}.get(f["status"], f["status"])
                files[n] = {"status": st, "tests": len(f["assertionResults"]),
                            "failed": sum(t["status"] == "failed" for t in f["assertionResults"]),
                            "duration_ms": round(f["endTime"] - f["startTime"])}
            return {"files": files}
        res = {"wall_s": round(time.time() - t0, 1), "times": (tmp / "out/_times.txt").read_text() if (tmp / "out/_times.txt").exists() else "",
               "suite1": sres("suite1.json"), "suite2": sres("suite2.json"), "tests": {}}
        idx = tmp / "out/_index.txt"
        for line in (idx.read_text().splitlines() if idx.exists() else []):
            f, rc, secs = line.split(); res["tests"][f] = {"exit": int(rc), "secs": int(secs), "covered": {}}
            cf = tmp / "out" / (f.replace("/", "_") + ".json")
            if not cf.exists(): continue
            for path, d in json.loads(cf.read_text()).items():
                lines = sorted({l for k, loc in d["statementMap"].items() if d["s"][k] > 0 for l in range(loc["start"]["line"], loc["end"]["line"] + 1)})
                if lines: res["tests"][f]["covered"][path.removeprefix("/repo/")] = lines
    return res

def gen_mutants(P, files):
    with tempfile.TemporaryDirectory() as wt:
        tar = pathlib.Path(wt) / "src.tar"
        subprocess.run(["git", "-C", str(repo), "archive", "-o", str(tar), P, "packages"], check=True)
        with tarfile.open(tar) as tf:
            tf.extractall(wt, filter="data", members=[m for m in tf.getmembers() if not (m.issym() or m.islnk())])
        r = subprocess.run(["node", str(M2 / "gen_mutants.mjs"), wt, *files], capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)
        return json.loads(r.stdout)

def run_mutants(P, jobs, tag):
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td); (tmp / "out").mkdir()
        subprocess.run(["git", "-C", str(repo), "archive", "-o", str(tmp / "src.tar"), P], check=True)
        (tmp / "jobs.json").write_text(json.dumps(jobs)); (tmp / "run_mutants.mjs").write_text((H / "run_mutants.mjs").read_text())
        script = f"tar -xf /in/src.tar -C /repo && cd /repo && {INSTALL} >&2 && node /in/run_mutants.mjs /in/jobs.json /out/res.json"
        t0 = time.time()
        p = docker(script, tmp)
        resf = tmp / "out/res.json"
        if not resf.exists(): raise RuntimeError(f"mutant run {tag} failed: " + p.stderr[-1500:])
        return {x["id"]: x for x in json.loads(resf.read_text())}, round(time.time() - t0, 1)

# pick commits
cands = []
for c in git("rev-list", "--no-merges", f"--since={a.since}", "HEAD").split():
    fs = git("diff-tree", "--no-commit-id", "--name-only", "-r", c).split()
    if any(any(f.startswith(p) for p in SRC_PREFIXES) and f.endswith(".ts") for f in fs) and git("rev-list", "--parents", "-n1", c).split()[1:]:
        cands.append(c)
random.Random(a.seed).shuffle(cands)
print(len(cands), "candidates", file=sys.stderr)

# augment pass: extra mutants on files not yet mutated, reusing persisted suite/coverage (no reruns)
if a.augment:
    for of in sorted(out.glob("[0-9a-f]*.json")):
        rec = json.loads(of.read_text())
        if "cov_P" not in rec or "suite_P" not in rec: continue
        if rec.get("augmented", 0) >= a.augment: continue
        P = rec["parent"]; _cur_image = rec.get("image") or image_for(P)
        covered = {t: v["covered"] for t, v in rec["cov_P"]["tests"].items()
                   if rec["suite_P"]["files"].get(t, {}).get("status") == "pass" and v["exit"] == 0}
        cnt = {}
        for t in covered:
            for f_, ls in covered[t].items():
                for l in ls: cnt[(f_, l)] = cnt.get((f_, l), 0) + 1
        already = {m["file"] for m in rec["mutants"]}
        srcs = sorted({f_ for (f_, l), n in cnt.items() if n >= a.min_cov and any(f_.startswith(p) for p in SRC_PREFIXES) and f_.endswith(".ts")} - already)
        ms = gen_mutants(P, srcs)
        byf = collections.defaultdict(list); rec["augment_below_min_cov"] = 0
        for m in ms:
            m["tests"] = sorted(t for t in covered if m["line"] in set(covered[t].get(m["file"], [])))
            if len(m["tests"]) >= a.min_cov: byf[m["file"]].append(m)
            else: rec["augment_below_min_cov"] += 1
        rng = random.Random(f"{a.seed}{P}:augment")
        order = sorted(byf); rng.shuffle(order)
        for f_ in order: rng.shuffle(byf[f_])
        meta = []
        while len(meta) < a.augment and any(byf[f_] for f_ in order):
            for f_ in order:
                if byf[f_] and len(meta) < a.augment: meta.append(byf[f_].pop())
        if not meta:
            rec["augmented"] = a.augment; of.write_text(json.dumps(rec)); continue
        jobs = [{"id": f"{m['file']}:{m['start']}:{m['mutator']}", "file": m["file"], "start": m["start"],
                 "end": m["end"], "replacement": m["replacement"], "tests": m["tests"]} for m in meta]
        res, mut_s = run_mutants(P, jobs, "augment")
        retry = [dict(j, split=True) for j in jobs if res.get(j["id"], {}).get("status") == "Error" and float(res[j["id"]].get("secs", 0)) >= 100]
        if retry:
            r2, s2b = run_mutants(P, retry, "augment-split"); mut_s += s2b
            res.update({k: v for k, v in r2.items()})
        rec.setdefault("stages", {})["augment_s"] = mut_s
        rec["mutants"].extend([{**{k: m[k] for k in ("file", "mutator", "line", "original", "replacement", "tests")},
                                "id": jobs[i]["id"], **{k: res.get(jobs[i]["id"], {}).get(k) for k in ("status", "killed_by_files", "secs", "via")}}
                               for i, m in enumerate(meta)])
        rec["n_mutant_files"] = len({m["file"] for m in rec["mutants"]})
        rec["augmented"] = rec.get("augmented", 0) + len(meta)
        of.write_text(json.dumps(rec))
        print("augmented", rec["commit"][:8], len(meta), "mutants on", len({m["file"] for m in meta}), "new files", file=sys.stderr)

done = 0
for c in ([] if a.augment else cands):
    if done >= a.n: break
    of = out / f"{c}.json"
    if of.exists(): done += 1; continue
    P = git("rev-parse", f"{c}^").strip()
    _cur_image = image_for(P)
    rec = {"commit": c, "parent": P, "image": _cur_image,
           "files_changed": git("diff-tree", "--no-commit-id", "--name-only", "-r", c).split(),
           "date": git("log", "-1", "--format=%cI", c).strip(), "stages": {}}
    try:
        scoped = [f for f in git("ls-tree", "-r", "--name-only", P, *TEST_PKGS).split() if ".test." in f]
        t0 = time.time()
        comb = suite_and_cov(P, sorted(scoped))
        rec["stages"]["combined_s"] = comb["wall_s"]; rec["stage_times"] = comb["times"]
        s1, s2 = comb["suite1"]["files"], comb["suite2"]["files"]
        allf = sorted(set(s1) | set(s2))
        green = {f for f in allf if s1.get(f, {}).get("status") == "pass" and s2.get(f, {}).get("status") == "pass"}
        rec["excluded_files"] = sorted(set(allf) - green)
        rec["suite_P"] = {"files": {t: {"status": "pass" if t in green else "fail",
                                        "duration_ms": s1.get(t, s2.get(t, {})).get("duration_ms", 0)} for t in allf}}
        rec["cov_P"] = {"tests": comb["tests"]}
        rec["n_cov_files"] = len(comb["tests"])
        covered = {t: v["covered"] for t, v in comb["tests"].items() if t in green and v["exit"] == 0}
        cnt = {}
        for t in covered:
            for f_, ls in covered[t].items():
                for l in ls: cnt[(f_, l)] = cnt.get((f_, l), 0) + 1
        srcs = sorted({f_ for (f_, l), n in cnt.items() if n >= a.min_cov and any(f_.startswith(p) for p in SRC_PREFIXES) and f_.endswith(".ts")})
        # selection-effect log: scoped src files with coverage but too few green covering tests to be mutated
        low = sorted({f_ for (f_, l), n in cnt.items() if n < a.min_cov and any(f_.startswith(p) for p in SRC_PREFIXES) and f_.endswith(".ts")})
        rec["src_files_below_min_cov"] = low; rec["n_src_files_eligible"] = len(srcs)
        ms = gen_mutants(P, srcs)
        byf = collections.defaultdict(list); rec["mutants_below_min_cov"] = 0
        for m in ms:
            m["tests"] = sorted(t for t in covered if m["line"] in set(covered[t].get(m["file"], [])))
            if len(m["tests"]) >= a.min_cov: byf[m["file"]].append(m)
            else: rec["mutants_below_min_cov"] += 1
        rng = random.Random(f"{a.seed}{P}")
        order = sorted(byf); rng.shuffle(order)
        for f_ in order: rng.shuffle(byf[f_])
        meta = []
        while len(meta) < a.per_commit and any(byf[f_] for f_ in order):
            for f_ in order:
                if byf[f_] and len(meta) < a.per_commit: meta.append(byf[f_].pop())
        rec["n_mutant_files"] = len({m["file"] for m in meta})
        jobs = [{"id": f"{m['file']}:{m['start']}:{m['mutator']}", "file": m["file"], "start": m["start"],
                 "end": m["end"], "replacement": m["replacement"], "tests": m["tests"]} for m in meta]
        t0 = time.time()
        res, mut_s = run_mutants(P, jobs, "batch")
        retry = [dict(j, split=True) for j in jobs if res.get(j["id"], {}).get("status") == "Error" and float(res[j["id"]].get("secs", 0)) >= 100]
        if retry:
            r2, s2b = run_mutants(P, retry, "split"); mut_s += s2b
            res.update({k: v for k, v in r2.items()})
        rec["stages"]["mutation_s"] = mut_s
        rec["mutants"] = [{**{k: m[k] for k in ("file", "mutator", "line", "original", "replacement", "tests")},
                           "id": jobs[i]["id"], **{k: res.get(jobs[i]["id"], {}).get(k) for k in ("status", "killed_by_files", "secs", "via")}}
                          for i, m in enumerate(meta)]
    except Exception as e:
        print("skip", c[:8], repr(e)[:300], file=sys.stderr); (out / f"{c}.skip").write_text(repr(e)); continue
    of.write_text(json.dumps(rec)); done += 1
    import collections; print("done", c[:8], dict(collections.Counter(x["status"] for x in rec["mutants"])), file=sys.stderr)

# summary
rows = [json.load(open(f)) for f in sorted(out.glob("[0-9a-f]*.json"))]
summ = {"n_commits": len(rows),
        "per_commit": [{"commit": r["commit"][:8], "parent": r["parent"][:8], "date": r["date"], "image": r.get("image"),
                        "combined_s": r["stages"].get("combined_s"), "mutation_s": r["stages"].get("mutation_s"),
                        "n_cov_files": r.get("n_cov_files"), "n_mutant_files": r.get("n_mutant_files"),
                        "excluded": r["excluded_files"], "mutants": len(r.get("mutants", [])),
                        "status": dict(collections.Counter(x["status"] for x in r.get("mutants", [])))} for r in rows]}
(out / "summary.json").write_text(json.dumps(summ, indent=1))
print(json.dumps(summ, indent=1))
