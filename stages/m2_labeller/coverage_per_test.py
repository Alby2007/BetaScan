#!/usr/bin/env python3
"""Per-test-file coverage at a commit. Usage: coverage_per_test.py REPO COMMIT OUT.json [--files a,b]
Runs each test file in isolation with v8 coverage inside Docker and records, per test file,
the covered line ranges of each src file (only lines with count>0, from istanbul-style coverage-final.json)."""
import argparse, json, pathlib, subprocess, sys, tempfile, time
ap = argparse.ArgumentParser()
ap.add_argument("repo"); ap.add_argument("commit"); ap.add_argument("out")
ap.add_argument("--files", default=""); ap.add_argument("--image", default="impactnet-node")
a = ap.parse_args()
repo = pathlib.Path(a.repo).resolve()
sha = subprocess.run(["git", "-C", str(repo), "rev-parse", a.commit], capture_output=True, text=True, encoding="utf-8", errors="replace", check=True).stdout.strip()
LOOP = r'''
set -u
tar -xf /in/src.tar -C /repo && cd /repo && pnpm install --frozen-lockfile >&2
FILES="$FILES_ENV"
[ -z "$FILES" ] && FILES=$(find test -name '*.test.ts' | sort | tr '\n' ',')
mkdir -p /out
for f in $(echo $FILES | tr ',' ' '); do
  rm -rf coverage
  s=$(date +%s)
  pnpm exec vitest --run --coverage --coverage.reporter=json --coverage.all=false "$f" >/tmp/log 2>&1; rc=$?
  n=$(echo "$f" | tr '/' '_')
  [ -f coverage/coverage-final.json ] && cp coverage/coverage-final.json /out/$n.json
  echo "$f $rc $(( $(date +%s)-s ))" >> /out/_index.txt
done
'''
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp); (tmp / "out").mkdir()
    subprocess.run(["git", "-C", str(repo), "archive", "-o", str(tmp / "src.tar"), sha], check=True)
    t0 = time.time()
    subprocess.run(["docker", "run", "--rm", "-v", f"{tmp}:/in", "-v", f"{tmp}/out:/out", "-v", "impactnet-pnpm-store:/root/.local/share/pnpm",
                    "-e", "CI=true", "-e", f"FILES_ENV={a.files}", a.image, "bash", "-c", LOOP], check=True, stderr=subprocess.DEVNULL)
    res = {"commit": sha, "wall_s": round(time.time() - t0, 1), "tests": {}}
    for line in (tmp / "out/_index.txt").read_text().splitlines():
        f, rc, secs = line.split(); res["tests"][f] = {"exit": int(rc), "secs": int(secs), "covered": {}}
        p = tmp / "out" / (f.replace("/", "_") + ".json")
        if not p.exists(): continue
        for path, d in json.loads(p.read_text()).items():
            lines = sorted({l for k, loc in d["statementMap"].items() if d["s"][k] > 0 for l in range(loc["start"]["line"], loc["end"]["line"] + 1)})
            if lines: res["tests"][f]["covered"][path.removeprefix("/repo/")] = lines
pathlib.Path(a.out).write_text(json.dumps(res))
print(a.out, res["wall_s"], "s", len(res["tests"]), "tests")
