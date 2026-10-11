#!/usr/bin/env python3
"""P2 repo screen (run BEFORE collection; produces the final list).
Per candidate repo: shallow clone -> detect runner/PM -> docker install ->
repo's own test command x2 -> plain `vitest run` if the script failed or chained
-> coverage smoke on one test file -> one line to screen.jsonl.
Exclusions appended to exclusions.jsonl with {repo, reason, stage:screen}.
Usage: screen_repo.py --list repos.txt [--timeout 1500]
repos.txt lines: <org>/<name> [<sha>]   (# comments ok)
"""
import argparse, collections, json, pathlib, re, shutil, subprocess, tarfile, tempfile, time

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

CMD_VERSION = "v8e-faildetail" # v8d + fail/signature detail taken from the best available attempt (canonical fail -> alt still gets classified)

import sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from domains import DOMAINS
from invoke import derive_invocation, normsig

def reason_of(msg):
    m = msg.lower()
    if re.search(r"econnrefused|enotfound|eai_again|fetch failed|socket|etimedout|\bnetwork\b", m): return "network"
    if re.search(r"jsdom|happy-dom|playwright|puppeteer|chromium|webgl|\bbrowser\b|document is not defined|window is not defined|localstorage", m): return "dom/browser"
    if re.search(r"cannot find module|err_module_not_found|no such file|/dist/|/build/", m): return "missing-build"
    if re.search(r"command not found|enoent|docker|permission denied", m): return "missing-tool"
    return "other"
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
    ok = (rec["install_ok"] and (rec["runner"] == "vitest")
          and (rec.get("frac_green_both") or 0) >= 0.9
          and (rec["vitest_s"] or 1e9) <= 600 and rec.get("cov_ok")
          and (rec.get("proj_harvest_s") or 1e9) <= 5400)
    if not ok:
        cls = "unscored" if rec.get("verdict") == "unscored" else "intrinsic"
        excl.write(json.dumps({"repo": rec["repo"], "reason": rec["reason"], "stage": "screen",
                               "class": cls}) + "\n"); excl.flush()
    else:
        rec["verdict"] = "pass"

LOOP = r'''
set -u
tar -xf /in/src.tar -C /repo 2>/dev/null || (mkdir -p /repo && tar -xf /in/src.tar -C /repo); cd /repo
case "$PM_ENV" in
  pnpm) pnpm install --frozen-lockfile >&2 || pnpm install >&2 ;;
  npm)  npm ci >&2 || npm install >&2 ;;
  yarn) yarn install --frozen-lockfile >&2 || yarn install >&2 ;;
esac || exit 9
# CI's prebuild step, if any (generic — no per-repo workarounds)
if [ -n "$PREBUILD_CMD" ]; then
  echo "prebuild: $PREBUILD_CMD" >&2; s=$(date +%s)
  timeout 900 bash -c "$PREBUILD_CMD" >&2
  echo "b $? $(( $(date +%s)-s ))" >> /out/_runs.txt
fi
# repo's own test command once (chain logging)
s=$(date +%s)
case "$PM_ENV" in
  pnpm) timeout 900 pnpm test >/out/test.log 2>&1 ;;
  npm)  timeout 900 npm test >/out/test.log 2>&1 ;;
  yarn) timeout 900 yarn test >/out/test.log 2>&1 ;;
esac
echo "t $? $(( $(date +%s)-s ))" >> /out/_runs.txt
# canonical vitest invocation x2 with per-file JSON (from CI/pkg/fallback)
for run in 1 2; do
  s=$(date +%s)
  timeout 900 bash -c "$VITEST_CMD=/out/vitest$run.json" >/out/vitest$run.log 2>&1
  echo "v$run $? $(( $(date +%s)-s ))" >> /out/_runs.txt
done
# config-level? (<3 passed files total) -> one retry with the alternate invocation
p=$(grep -oh '"status": *"passed"' /out/vitest1.json /out/vitest2.json 2>/dev/null | wc -l)
EFF="$VITEST_CMD"
if [ "$p" -lt 3 ] && [ -n "$ALT_VITEST_CMD" ]; then
  s=$(date +%s)
  timeout 900 bash -c "$ALT_VITEST_CMD=/out/vitest_alt.json" >/out/vitest_alt.log 2>&1
  echo "va $? $(( $(date +%s)-s ))" >> /out/_runs.txt
  pa=$(grep -oh '"status": *"passed"' /out/vitest_alt.json 2>/dev/null | wc -l)
  [ "$pa" -ge 3 ] && EFF="$ALT_VITEST_CMD"
fi
# coverage provider: install @vitest/coverage-v8 at the installed vitest version if missing (HARNESS patch)
VVER=$(node -e "try{console.log(require('vitest/package.json').version)}catch(e){console.log('x')}" 2>/dev/null)
PINST=0
if ! node -e "require.resolve('@vitest/coverage-v8')" 2>/dev/null; then
  case "$PM_ENV" in
    pnpm) pnpm add -D "@vitest/coverage-v8@$VVER" >&2 && PINST=1 ;;
    npm)  npm i -D "@vitest/coverage-v8@$VVER" >&2 && PINST=1 ;;
    yarn) yarn add -D "@vitest/coverage-v8@$VVER" >&2 && PINST=1 ;;
  esac
fi
echo "p $VVER $PINST" >> /out/_runs.txt
# coverage smoke: ~5 test files stratified by size (harvest-critical); scope dir preferred
find . -path ./node_modules -prune -o \( -name '*.test.*' -o -name '*.spec.*' \) -printf '%s %p\n' | sort -n > /tmp/tf_all.txt
if [ -n "$COV_DIR" ]; then grep "$COV_DIR" /tmp/tf_all.txt > /tmp/tf.txt; [ -s /tmp/tf.txt ] || cp /tmp/tf_all.txt /tmp/tf.txt;
else cp /tmp/tf_all.txt /tmp/tf.txt; fi
wc -l < /tmp/tf.txt > /out/_ntests.txt
n=$(wc -l < /tmp/tf.txt)
for i in 0 1 2 3 4; do
  [ "$n" -gt 0 ] || break
  idx=$(( 1 + i*(n-1)/4 )); [ "$idx" -gt "$n" ] && idx=$n
  f=$(awk "NR==$idx" /tmp/tf.txt | cut -d' ' -f2-)
  s=$(date +%s); rm -rf coverage
  timeout 300 bash -c "$COV_CMD --coverage --coverage.reporter=json --coverage.all=false \"$f\" --reporter=json --outputFile=/out/covres_$i.json" >/out/cov_$i.log 2>&1
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
           "test_rc": None, "test_s": None, "vitest_runs": {}, "vitest_s": None,
           "verdict": None, "harness_patches": {},
           "cov_ok": None, "cov_files": [], "proj_harvest_s": None,
           "frac_green_both": None, "n_files_run": None, "files_flaky": [], "files_fail": {},
           "fail_reasons": {}, "domain": DOMAINS.get(repo, "?"), "n_test_files": None, "reason": None}
    try:
        if dest.exists() and run(["git", "-C", str(dest), "rev-parse", "--verify", "HEAD"]).returncode:
            shutil.rmtree(dest, ignore_errors=True)  # stale/mid-clone leftover
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
        vpre, alt, prebuild, src, cand, scope = derive_invocation(dest, rec["pm"])
        cov_cmd = (f"{rec['pm']} exec vitest run" if rec["pm"] == "pnpm"
                   else "yarn vitest run" if rec["pm"] == "yarn" else "npx --no-install vitest run")
        rec.update({"invoke": vpre, "invoke_src": src, "invoke_alt": alt,
                    "prebuild": prebuild, "prebuild_s": 0, "ci_steps": cand,
                    "cov_node_frac": None, "cov_dir": scope})
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp); (tmp / "out").mkdir()
            subprocess.run(["git", "-C", str(dest), "archive", "-o", str(tmp / "src.tar"), "HEAD"], check=True)
            t0 = time.time()
            run(["docker", "run", "--rm", "-v", f"{tmp}:/in", "-v", f"{tmp}/out:/out",
                 "-v", f"{a.pnpm_store}:/root/.local/share/pnpm",
                 "-e", "CI=true", "-e", f"PM_ENV={rec['pm']}", "-e", f"VITEST_CMD={vpre}",
                 "-e", f"ALT_VITEST_CMD={alt}", "-e", f"PREBUILD_CMD={prebuild}", "-e", f"COV_DIR={scope}",
                 "-e", f"COV_CMD={cov_cmd}",
                 a.image, "bash", "-c", LOOP], timeout=a.timeout)
            rec["suite_wall_s"] = round(time.time() - t0, 1)
            runs_txt = tmp / "out/_runs.txt"
            if not runs_txt.exists():
                rec["reason"] = "install_or_suite_fail"; emit(rec); continue
            rec["install_ok"] = True
            for l in runs_txt.read_text().splitlines():
                p_ = l.split()
                if p_[0] == "c":
                    rec["cov_files"].append({"rc": int(p_[1]), "secs": int(p_[2]), "ok": int(p_[3])})
                elif p_[0] == "t":
                    rec["test_rc"], rec["test_s"] = int(p_[1]), int(p_[2])
                elif p_[0] == "b":
                    rec["prebuild_s"] = int(p_[2])
                elif p_[0] == "p":
                    if len(p_) > 2 and p_[2] == "1" and p_[1] != "x":
                        rec["harness_patches"]["@vitest/coverage-v8"] = p_[1]
                else:  # v1, v2
                    rec["vitest_runs"][p_[0]] = {"rc": int(p_[1]), "secs": int(p_[2])}
            nt = tmp / "out/_ntests.txt"
            rec["n_test_files"] = int(nt.read_text().strip()) if nt.exists() else None

            def filestatus(f):
                try: j = json.loads(f.read_text(encoding="utf-8"))
                except Exception: return {}
                out = {}
                for tr in j.get("testResults", []):
                    name = tr.get("name", "").split("/repo/")[-1]
                    out[name] = (tr.get("status") == "passed", json.dumps(tr)[:4000])
                return out
            r1 = filestatus(tmp / "out/vitest1.json"); r2 = filestatus(tmp / "out/vitest2.json")
            if r1 and r2:
                allf = set(r1) | set(r2)
                green = {f for f in allf if r1.get(f, (0,))[0] and r2.get(f, (0,))[0]}
                flaky = {f for f in allf if ((f in r1) != (f in r2)) or
                         (f in r1 and f in r2 and r1[f][0] != r2[f][0])}
                failf = allf - green - flaky
                rec["n_files_run"] = len(allf)
                rec["files_green_both"] = len(green)
                rec["frac_green_both"] = round(len(green) / max(1, len(allf)), 3)
                rec["files_flaky"] = sorted(flaky)
                rec["files_fail"] = {f: reason_of(r1.get(f, (0, ""))[1] + r2.get(f, (0, ""))[1])
                                     for f in sorted(failf)}
                rec["fail_reasons"] = dict(collections.Counter(rec["files_fail"].values()))
                rec["fail_sigs"] = dict(collections.Counter(
                    normsig(r1.get(f, (0, ""))[1] + r2.get(f, (0, ""))[1]) for f in failf).most_common(5))
                rec["config_level"] = len(rec["fail_sigs"]) == 1 and len(failf) >= 5
                rec["attempts"] = [{"invoke": vpre, "src": src, "frac": rec["frac_green_both"], "runs": 2}]
                rec["vitest_s"] = rec["vitest_runs"].get("v1", {}).get("secs")
            rec["vitest_s"] = rec["vitest_s"] or rec["vitest_runs"].get("va", {}).get("secs")
            ralt = filestatus(tmp / "out/vitest_alt.json")
            if ralt:
                allfa = set(ralt)
                fa = round(sum(1 for f in allfa if ralt[f][0]) / max(1, len(allfa)), 3)
                rec.setdefault("attempts", []).append({"invoke": alt, "src": "alt-fallback", "frac": fa, "runs": 1})
                if fa > (rec.get("frac_green_both") or 0):
                    rec["frac_green_both"], rec["n_files_run"], rec["rescue"] = fa, len(allfa), True
            if not rec.get("files_fail") and not rec.get("files_flaky"):
                best = ralt or (r1 if len(r1) >= len(r2) else r2)
                failf = {f for f, (ok, _) in best.items() if not ok}
                rec["files_fail"] = {f: reason_of(best[f][1]) for f in sorted(failf)}
                rec["fail_reasons"] = dict(collections.Counter(rec["files_fail"].values()))
                rec["fail_sigs"] = dict(collections.Counter(normsig(best[f][1]) for f in failf).most_common(5))
            covs = rec["cov_files"]
            if covs:
                med = sorted(c["secs"] for c in covs)[len(covs) // 2]
                rec["cov_ok"] = sum(c["ok"] for c in covs) > 0
                rec["proj_harvest_s"] = med * (rec["n_files_run"] or rec["n_test_files"] or 0) + rec["prebuild_s"]
            # coverage -> graph-node match: fraction of covered files present as graph file nodes.
            # Low ratio = coverage landing on dist/built files the source graph can't match (QA flag).
            covf = next((p for p in sorted(tmp.glob("out/cov_*.json"))
                         if not p.name.startswith("covres")), None)
            if covf:
                try:
                    g = run(["node", str(pathlib.Path(__file__).parents[1] / "m1_extractor" / "extract.mjs"),
                             str(dest), rec["sha"] or "HEAD"], timeout=600)
                    files = {n["file"] for n in json.loads(g.stdout).get("nodes", []) if n.get("file")}
                    covd = {k.split("/repo/")[-1] for k in json.loads(covf.read_text(encoding="utf-8"))}
                    rec["cov_node_frac"] = round(len(covd & files) / max(1, len(covd)), 3)
                except Exception as e:
                    rec["cov_node_frac"] = f"err:{e}"
            frac = rec.get("frac_green_both")
            if frac is None:
                ran = max((r.get("secs", 0) for r in rec["vitest_runs"].values()), default=0)
                if ran > 20:
                    rec["verdict"], rec["reason"] = "unscored", f"unscored: tests ran ~{ran}s, no JSON output"
                else:
                    rec["reason"] = "no JSON, invocation fails both attempts"
            elif frac < 0.9: rec["reason"] = (f"only {frac:.0%} files green both runs {rec['fail_reasons']}"
                                            f" sigs={rec.get('fail_sigs')}")
            elif (rec["vitest_s"] or 1e9) > 600: rec["reason"] = f"suite {rec['vitest_s']}s > 600s"
            elif not rec["cov_ok"]:
                lg = next((p for p in sorted(tmp.glob("out/cov_*.log"))), None)
                txt = lg.read_text(encoding="utf-8", errors="replace") if lg else ""
                errs = [l.strip() for l in txt.splitlines()
                        if re.search(r"error|Error|Cannot|MISSING|missing|failed|not found", l)]
                rec["cov_err"] = " | ".join(errs[:3])[:400] if errs else " ".join(txt.split())[-300:]
                rec["reason"] = "coverage smoke failed"
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
