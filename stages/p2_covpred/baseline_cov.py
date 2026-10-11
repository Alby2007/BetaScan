#!/usr/bin/env python3
"""Baseline coverage: what does an EMPTY test execute? (setup files, global setup, framework init)
Runs a stub test file with v8 coverage inside Docker; output matches coverage_per_test.py format
(tests -> covered -> file -> [lines]) so pairs.py can subtract it from labels.
Usage: baseline_cov.py REPO COMMIT OUT.json --stub test/_baseline_cov.test.ts [--image impactnet-node] [--filter DIR]"""
import argparse, json, pathlib, subprocess, tempfile, time
ap = argparse.ArgumentParser()
ap.add_argument("repo"); ap.add_argument("commit"); ap.add_argument("out")
ap.add_argument("--stub", default="test/_baseline_cov.test.ts")
ap.add_argument("--image", default="impactnet-node")
ap.add_argument("--filter", default="", help="positional vitest filter dirs (trpc uses package dirs)")
a = ap.parse_args()
repo = pathlib.Path(a.repo).resolve()
sha = subprocess.run(["git", "-C", str(repo), "rev-parse", a.commit], capture_output=True, text=True, encoding="utf-8", errors="replace", check=True).stdout.strip()
stub_dir = a.stub.rsplit("/", 1)[0]
LOOP = r'''
set -u
tar -xf /in/src.tar -C /repo && cd /repo && pnpm install --frozen-lockfile >&2
mkdir -p "$STUBDIR"
printf 'import {test} from "vitest";\ntest("baseline-coverage-probe",()=>{});\n' > "$STUB"
rm -rf coverage
s=$(date +%s)
pnpm exec vitest --run --coverage --coverage.reporter=json --coverage.all=false $FILT "$STUB" >/tmp/log 2>&1; rc=$?
cat /tmp/log >&2
n=$(echo "$STUB" | tr '/' '_')
mkdir -p /out
[ -f coverage/coverage-final.json ] && cp coverage/coverage-final.json /out/$n.json
echo "$STUB $rc $(( $(date +%s)-s ))" >> /out/_index.txt
'''
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp); (tmp / "out").mkdir()
    subprocess.run(["git", "-C", str(repo), "archive", "-o", str(tmp / "src.tar"), sha], check=True)
    t0 = time.time()
    subprocess.run(["docker", "run", "--rm", "-v", f"{tmp}:/in", "-v", f"{tmp}/out:/out", "-v", "impactnet-pnpm-store:/root/.local/share/pnpm",
                    "-e", "CI=true", "-e", f"STUB={a.stub}", "-e", f"STUBDIR={stub_dir}", "-e", f"FILT={a.filter}",
                    a.image, "bash", "-c", LOOP], check=True)
    res = {"commit": sha, "wall_s": round(time.time() - t0, 1), "tests": {}}
    for line in (tmp / "out/_index.txt").read_text().splitlines():
        f, rc, secs = line.split(); res["tests"][f] = {"exit": int(rc), "secs": int(secs), "covered": {}}
        p = tmp / "out" / (f.replace("/", "_") + ".json")
        if not p.exists(): continue
        for path, d in json.loads(p.read_text()).items():
            lines = sorted({l for k, loc in d["statementMap"].items() if d["s"][k] > 0 for l in range(loc["start"]["line"], loc["end"]["line"] + 1)})
            if lines: res["tests"][f]["covered"][path.removeprefix("/repo/")] = lines
pathlib.Path(a.out).write_text(json.dumps(res))
print(a.out, res["wall_s"], "s;", {t: v["exit"] for t, v in res["tests"].items()})
