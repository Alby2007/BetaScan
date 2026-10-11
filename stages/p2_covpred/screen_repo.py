#!/usr/bin/env python3
"""P2 repo screen (run BEFORE collection; produces the final list).
Per candidate repo: shallow clone -> detect runner/PM -> docker install -> vitest
run x2 (json reporter) -> one line to screen.jsonl. Exclusions appended to
exclusions.jsonl with {repo, reason, stage:screen}.
Usage: screen_repo.py --list repos.txt [--timeout 1500] [--jobs 1]
repos.txt lines: <org>/<name> [<sha>]   (# comments ok)
"""
import argparse, json, pathlib, subprocess, sys, tarfile, tempfile, time

ap = argparse.ArgumentParser()
ap.add_argument("--list", required=True)
ap.add_argument("--timeout", type=int, default=1500)
ap.add_argument("--out", default="data/covpred/screen.jsonl")
ap.add_argument("--excl", default="data/covpred/exclusions.jsonl")
ap.add_argument("--image", default="impactnet-node")
ap.add_argument("--clone-dir", default="targets_screen")
a = ap.parse_args()

ROOT = pathlib.Path(a.clone_dir); ROOT.mkdir(exist_ok=True)
pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
screen = open(a.out, "a", encoding="utf-8"); excl = open(a.excl, "a", encoding="utf-8")
CMD_VERSION = "v2-testscript"   # v1 ran root `npx vitest`; v2 runs the repo's own test script
RETRY = {"install_or_suite_fail", "timeout", "error", "clone_fail"}
done = set()
if pathlib.Path(a.out).exists():
    keep = []
    for l in open(a.out, encoding="utf-8"):
        r = json.loads(l)
        if r.get("cmd") != CMD_VERSION or any(str(r.get("reason") or "").startswith(x) for x in RETRY):
            continue  # stale command version or retryable failure -> re-screen
        done.add(r["repo"]); keep.append(l)
    pathlib.Path(a.out).write_text("".join(keep), encoding="utf-8")

def emit(rec):
    screen.write(json.dumps(rec) + "\n"); screen.flush()
    if not (rec["install_ok"] and rec["runner"] == "vitest" and not rec["flaky"] and rec["suite_wall_s"] <= 600):
        excl.write(json.dumps({"repo": rec["repo"], "reason": rec["reason"], "stage": "screen"}) + "\n"); excl.flush()

LOOP = r'''
set -u
tar -xf /in/src.tar -C /repo 2>/dev/null && cd /repo
case "$PM_ENV" in
  pnpm) pnpm install --frozen-lockfile >&2 || pnpm install >&2 ;;
  npm)  npm ci >&2 || npm install >&2 ;;
  yarn) yarn install --frozen-lockfile >&2 || yarn install >&2 ;;
esac
for run in 1 2; do
  s=$(date +%s)
  case "$PM_ENV" in
    pnpm) pnpm test -- --reporter=json --outputFile=/out/run$run.json >/out/run$run.log 2>&1 ;;
    npm)  npm test -- --reporter=json --outputFile=/out/run$run.json >/out/run$run.log 2>&1 ;;
    yarn) yarn test --reporter=json --outputFile=/out/run$run.json >/out/run$run.log 2>&1 ;;
  esac
  rc=$?
  [ ! -s /out/run$run.json ] && npx vitest run --reporter=json --outputFile=/out/run$run.json >>/out/run$run.log 2>&1 && rc=$?
  echo "$run $rc $(( $(date +%s)-s ))" >> /out/_runs.txt
done
find . -path ./node_modules -prune -o -name '*.test.*' -print -o -name '*.spec.*' -print | wc -l > /out/_ntests.txt
'''

def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)

for line in open(a.list, encoding="utf-8"):
    line = line.split("#")[0].strip()
    if not line: continue
    parts = line.split(); repo = parts[0]; sha = parts[1] if len(parts) > 1 else None
    if repo in done: continue
    name = repo.replace("/", "__"); dest = ROOT / name
    rec = {"repo": repo, "cmd": CMD_VERSION, "runner": None, "pm": None, "install_ok": False, "suite_wall_s": None,
           "runs": [], "flaky": None, "n_test_files": None, "reason": None}
    try:
        if not dest.exists():
            r = run(["git", "clone", "--depth", "1", f"https://github.com/{repo}.git", str(dest)], timeout=300)
            if r.returncode: rec["reason"] = "clone_fail: " + r.stderr.strip()[:200]; emit(rec); continue
        # local checks: runner + PM
        pj = dest / "package.json"
        pkgs = [json.loads(pj.read_text(encoding="utf-8"))] if pj.exists() else []
        scripts = " ".join(str(v) for p in pkgs for v in p.get("scripts", {}).values())
        has_vitest_cfg = any(dest.glob("**/vitest*.[jt]s")) or any(dest.glob("**/vitest*.workspace.*"))
        if "vitest" in scripts or has_vitest_cfg or any("vitest" in json.dumps(p.get("devDependencies", {})) for p in pkgs):
            rec["runner"] = "vitest"
        else:
            for r_ in ("jest", "mocha", "ava", "tap", "bun", "node --test", "node:test"):
                if r_ in scripts: rec["runner"] = r_; break
            rec["runner"] = rec["runner"] or "unknown"
            rec["reason"] = f"runner={rec['runner']}"; emit(rec); continue
        rec["pm"] = "pnpm" if (dest / "pnpm-lock.yaml").exists() else "yarn" if (dest / "yarn.lock").exists() else "npm"
        # docker screen
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp); (tmp / "out").mkdir()
            subprocess.run(["git", "-C", str(dest), "archive", "-o", str(tmp / "src.tar"), "HEAD"], check=True)
            t0 = time.time()
            r = run(["docker", "run", "--rm", "-v", f"{tmp}:/in", "-v", f"{tmp}/out:/out",
                     "-v", "impactnet-pnpm-store:/root/.local/share/pnpm",
                     "-e", "CI=true", "-e", f"PM_ENV={rec['pm']}", a.image, "bash", "-c", LOOP], timeout=a.timeout)
            wall = round(time.time() - t0, 1)
            runs_txt = tmp / "out/_runs.txt"
            if not runs_txt.exists():
                rec["reason"] = "install_or_suite_fail"; emit(rec); continue
            rec["install_ok"] = True
            passes = []
            for l in runs_txt.read_text().splitlines():
                n, rc, secs = l.split(); j = tmp / "out" / f"run{n}.json"
                res = {"run": int(n), "rc": int(rc), "secs": int(secs)}
                if j.exists():
                    d = json.loads(j.read_text(encoding="utf-8", errors="replace"))
                    res.update(pass_=d.get("numPassedTests"), fail=d.get("numFailedTests"), total=d.get("numTotalTests"))
                    passes.append((d.get("numPassedTests"), d.get("numFailedTests"), d.get("numTotalTests")))
                rec["runs"].append(res)
            nt = tmp / "out/_ntests.txt"
            rec["n_test_files"] = int(nt.read_text().strip()) if nt.exists() else None
            rec["suite_wall_s"] = wall
            rec["flaky"] = len(set(passes)) > 1 if len(passes) == 2 else None
            if rec["flaky"]: rec["reason"] = "flaky: run1!=run2"
            elif rec["suite_wall_s"] > 600: rec["reason"] = f"suite {wall}s > 600s"
            elif any(x["rc"] != 0 for x in rec["runs"]): rec["reason"] = "vitest nonzero exit"
            emit(rec)
    except subprocess.TimeoutExpired:
        rec["reason"] = f"timeout {a.timeout}s"; emit(rec)
    except Exception as e:
        rec["reason"] = f"error: {e}"; emit(rec)
    print(repo, "->", rec["reason"] or "PASS", flush=True)
screen.close(); excl.close()
