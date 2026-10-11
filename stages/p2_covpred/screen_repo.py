#!/usr/bin/env python3
"""P2 repo screen (run BEFORE collection; produces the final list).
Per candidate repo: shallow clone -> detect runner/PM -> docker install ->
repo's own test command x2 -> plain `vitest run` if the script failed or chained
-> coverage smoke on one test file -> one line to screen.jsonl.
Exclusions appended to exclusions.jsonl with {repo, reason, stage:screen}.
Usage: screen_repo.py --list repos.txt [--timeout 1500]
repos.txt lines: <org>/<name> [<sha>]   (# comments ok)
"""
import argparse, json, pathlib, shutil, subprocess, tarfile, tempfile, time

ap = argparse.ArgumentParser()
ap.add_argument("--list", required=True)
ap.add_argument("--timeout", type=int, default=1500)
ap.add_argument("--out", default="data/covpred/screen.jsonl")
ap.add_argument("--excl", default="data/covpred/exclusions.jsonl")
ap.add_argument("--image", default="impactnet-node")
ap.add_argument("--clone-dir", default="A:/BetaScan_screen")
ap.add_argument("--pnpm-store", default="A:/pnpm-store")
ap.add_argument("--c-min-gb", type=float, default=10.0)
a = ap.parse_args()

CMD_VERSION = "v4-sha5cov"   # v3 + head SHA, 5-file coverage median, A:-pause, 90min projection
RETRY = {"install_or_suite_fail", "timeout", "error", "clone_fail", "disk_guard"}
ROOT = pathlib.Path(a.clone_dir); ROOT.mkdir(exist_ok=True)
pathlib.Path(a.pnpm_store).mkdir(parents=True, exist_ok=True)
pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
screen = open(a.out, "a", encoding="utf-8"); excl = open(a.excl, "a", encoding="utf-8")

def wait_a(max_s=7200):
    t0 = time.time()
    while not pathlib.Path(a.clone_dir.split(":")[0] + ":/").exists():
        if time.time() - t0 > max_s: return False
        print("A: unavailable — pausing", flush=True); time.sleep(60)
    return True

done = set()
if pathlib.Path(a.out).exists():
    keep = []
    for l in open(a.out, encoding="utf-8"):
        r = json.loads(l)
        if r.get("cmd") != CMD_VERSION or any(str(r.get("reason") or "").startswith(x) for x in RETRY):
            continue  # stale command version or retryable failure -> re-screen
        done.add(r["repo"]); keep.append(l)
    pathlib.Path(a.out).write_text("".join(keep), encoding="utf-8")

# image provenance for meta records (digest-pinned bases live in docker/Dockerfile*)
def img_meta(img):
    r = subprocess.run(["docker", "image", "inspect", img, "--format", "{{index .RepoDigests 0}}"],
                       capture_output=True, text=True)
    v = subprocess.run(["docker", "run", "--rm", img, "bash", "-c", "node -v; pnpm -v"],
                       capture_output=True, text=True).stdout.split()
    return {"image": img, "image_digest": r.stdout.strip(), "node": v[0] if v else "", "pnpm": v[1] if len(v) > 1 else ""}
IMG = img_meta(a.image)

CHAIN_HINTS = ("lint", "tsc", "typecheck", "type-check", "format", "build", "attw", "publint")
def emit(rec):
    screen.write(json.dumps(rec) + "\n"); screen.flush()
    ok = (rec["install_ok"] and (rec["runner"] == "vitest") and not rec["flaky"]
          and (rec["vitest_s"] or 1e9) <= 600 and rec.get("cov_ok")
          and (rec["vitest_rc"] == 0)
          and (rec.get("proj_harvest_s") or 1e9) <= 5400)
    if not ok:
        excl.write(json.dumps({"repo": rec["repo"], "reason": rec["reason"], "stage": "screen"}) + "\n"); excl.flush()

LOOP = r'''
set -u
tar -xf /in/src.tar -C /repo 2>/dev/null || (mkdir -p /repo && tar -xf /in/src.tar -C /repo); cd /repo
case "$PM_ENV" in
  pnpm) pnpm install --frozen-lockfile >&2 || pnpm install >&2 ;;
  npm)  npm ci >&2 || npm install >&2 ;;
  yarn) yarn install --frozen-lockfile >&2 || yarn install >&2 ;;
esac || exit 9
# repo's own test command x2 (flaky check + wall)
for run in 1 2; do
  s=$(date +%s)
  case "$PM_ENV" in
    pnpm) pnpm test >/out/test$run.log 2>&1 ;;
    npm)  npm test >/out/test$run.log 2>&1 ;;
    yarn) yarn test >/out/test$run.log 2>&1 ;;
  esac
  echo "$run $? $(( $(date +%s)-s ))" >> /out/_runs.txt
done
# plain vitest run (what harvest uses) — always, for classification + timing
s=$(date +%s)
npx vitest run --reporter=json --outputFile=/out/vitest.json >/out/vitest.log 2>&1
echo "v $? $(( $(date +%s)-s ))" >> /out/_runs.txt
# coverage smoke: ~5 test files stratified by size (harvest-critical)
find . -path ./node_modules -prune -o \( -name '*.test.*' -o -name '*.spec.*' \) -printf '%s %p\n' | sort -n > /tmp/tf.txt
wc -l < /tmp/tf.txt > /out/_ntests.txt
n=$(wc -l < /tmp/tf.txt)
for i in 0 1 2 3 4; do
  [ "$n" -gt 0 ] || break
  idx=$(( 1 + i*(n-1)/4 )); [ "$idx" -gt "$n" ] && idx=$n
  f=$(awk "NR==$idx" /tmp/tf.txt | cut -d' ' -f2-)
  s=$(date +%s); rm -rf coverage
  npx vitest run --coverage --coverage.reporter=json --coverage.all=false "$f" >/out/cov_$i.log 2>&1
  ok=0; [ -f coverage/coverage-final.json ] && ok=1 && cp coverage/coverage-final.json /out/cov_$i.json
  echo "c $? $(( $(date +%s)-s )) $ok" >> /out/_runs.txt
done
'''

def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)

for line in open(a.list, encoding="utf-8"):
    line = line.split("#")[0].strip()
    if not line: continue
    parts = line.split(); repo = parts[0]
    if repo in done: continue
    if not wait_a():
        print("A: still gone — aborting"); break
    if shutil.disk_usage("C:/").free < a.c_min_gb * (1 << 30):
        print("C: below", a.c_min_gb, "GB — aborting"); break
    dest = ROOT / repo.replace("/", "__")
    rec = {"repo": repo, "cmd": CMD_VERSION, **IMG, "runner": None, "pm": None, "sha": None,
           "test_script": None, "chains": [], "install_ok": False, "suite_wall_s": None,
           "runs": [], "vitest_rc": None, "vitest_s": None, "cov_ok": None, "cov_files": [],
           "proj_harvest_s": None, "flaky": None, "n_test_files": None, "reason": None}
    try:
        if not dest.exists():
            r = run(["git", "clone", "--depth", "1", f"https://github.com/{repo}.git", str(dest)], timeout=300)
            if r.returncode: rec["reason"] = "clone_fail: " + r.stderr.strip()[:200]; emit(rec); continue
        rec["sha"] = run(["git", "-C", str(dest), "rev-parse", "HEAD"]).stdout.strip()
        pj = dest / "package.json"
        pkgs = [json.loads(pj.read_text(encoding="utf-8"))] if pj.exists() else []
        scripts = {k: v for p in pkgs for k, v in p.get("scripts", {}).items()}
        rec["test_script"] = scripts.get("test")
        rec["chains"] = [s for s in str(scripts.get("test", "")).split("&&") if any(h in s for h in CHAIN_HINTS)]
        alltxt = " ".join(scripts.values()) + " " + " ".join(json.dumps(p.get("devDependencies", {})) for p in pkgs)
        has_vitest_cfg = any(dest.glob("**/vitest*.[jt]s")) or any(dest.glob("**/vitest*.workspace.*"))
        if "vitest" in alltxt or has_vitest_cfg:
            rec["runner"] = "vitest"
        else:
            for r_ in ("jest", "mocha", "ava", "tap", "bun", "node --test", "node:test"):
                if r_ in alltxt: rec["runner"] = r_; break
            rec["runner"] = rec["runner"] or "unknown"
            rec["reason"] = f"runner={rec['runner']}"; emit(rec); continue
        rec["pm"] = "pnpm" if (dest / "pnpm-lock.yaml").exists() else "yarn" if (dest / "yarn.lock").exists() else "npm"
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp); (tmp / "out").mkdir()
            subprocess.run(["git", "-C", str(dest), "archive", "-o", str(tmp / "src.tar"), "HEAD"], check=True)
            t0 = time.time()
            run(["docker", "run", "--rm", "-v", f"{tmp}:/in", "-v", f"{tmp}/out:/out",
                 "-v", f"{a.pnpm_store}:/root/.local/share/pnpm",
                 "-e", "CI=true", "-e", f"PM_ENV={rec['pm']}", a.image, "bash", "-c", LOOP], timeout=a.timeout)
            rec["suite_wall_s"] = round(time.time() - t0, 1)
            runs_txt = tmp / "out/_runs.txt"
            if not runs_txt.exists():
                rec["reason"] = "install_or_suite_fail"; emit(rec); continue
            rec["install_ok"] = True
            passes = []
            for l in runs_txt.read_text().splitlines():
                p_ = l.split()
                if p_[0] == "c":
                    rec["cov_files"].append({"rc": int(p_[1]), "secs": int(p_[2]), "ok": int(p_[3])})
                    continue
                if p_[0] == "v":
                    rec["vitest_rc"] = int(p_[1]); rec["vitest_s"] = int(p_[2]); continue
                res = {"run": int(p_[0]), "rc": int(p_[1]), "secs": int(p_[2])}
                rec["runs"].append(res)
                # classify pass/fail from the repo command's exit codes only (log text varies)
                passes.append(int(p_[1]))
            nt = tmp / "out/_ntests.txt"
            rec["n_test_files"] = int(nt.read_text().strip()) if nt.exists() else None
            covs = [c for c in rec["cov_files"]]
            if covs:
                med = sorted(c["secs"] for c in covs)[len(covs) // 2]
                rec["cov_ok"] = sum(c["ok"] for c in covs) > 0
                rec["proj_harvest_s"] = med * (rec["n_test_files"] or 0)
            rec["flaky"] = len(set(passes)) > 1 if len(passes) == 2 else None
            if rec["flaky"]: rec["reason"] = "flaky: run1!=run2"
            elif (rec["vitest_s"] or 1e9) > 600: rec["reason"] = f"suite {rec['vitest_s']}s > 600s"
            elif rec["vitest_rc"] != 0: rec["reason"] = f"vitest rc={rec['vitest_rc']}"
            elif not rec["cov_ok"]: rec["reason"] = "coverage smoke failed"
            elif (rec["proj_harvest_s"] or 1e9) > 5400: rec["reason"] = f"projected harvest {rec['proj_harvest_s']}s > 5400s"
            emit(rec)
    except subprocess.TimeoutExpired:
        rec["reason"] = f"timeout {a.timeout}s"; emit(rec)
    except Exception as e:
        rec["reason"] = f"error: {e}"; emit(rec)
    finally:
        if dest.exists():
            try: shutil.rmtree(dest)
            except Exception: pass  # delete clone+node_modules regardless of outcome
    print(repo, "->", rec["reason"] or "PASS", flush=True)
screen.close(); excl.close()
