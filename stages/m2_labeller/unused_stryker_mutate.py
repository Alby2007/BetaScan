#!/usr/bin/env python3
"""Run Stryker (vitest runner, perTest coverage, no bail) on selected files at a commit, inside Docker.
Usage: mutate.py REPO COMMIT OUT.json --files src/utils/cookie.ts,src/utils/query.ts
Output: {commit, wall_s, mutants:[{id,file,mutator,line,col,status,killed_by_files:[...]}]}"""
import argparse, json, pathlib, subprocess, tempfile, time
ap = argparse.ArgumentParser(); ap.add_argument("repo"); ap.add_argument("commit"); ap.add_argument("out")
ap.add_argument("--files", required=True); ap.add_argument("--image", default="impactnet-node"); ap.add_argument("--concurrency", default="4"); ap.add_argument("--exclude", default="test/utils.test.ts,test/rules/match.test.ts", help="test files not green at P (excluded; Stryker needs a green dry run)")
a = ap.parse_args(); repo = pathlib.Path(a.repo).resolve()
sha = subprocess.run(["git", "-C", str(repo), "rev-parse", a.commit], capture_output=True, text=True, check=True).stdout.strip()
mut = json.dumps(a.files.split(","))
exc = json.dumps([e for e in a.exclude.split(",") if e])
CFG = f'''export default {{ testRunner: "vitest", plugins: ["@stryker-mutator/vitest-runner"], coverageAnalysis: "perTest",
 mutate: {mut}, reporters: ["json"], jsonReporter: {{ fileName: "/out/report.json" }}, disableBail: true, concurrency: {a.concurrency},
 timeoutMS: 20000, tempDirName: "/tmp/stryker-tmp", ignoreStatic: true,
 vitest: {{ configFile: "vitest.stryker.config.mjs" }} }};'''
SCRIPT = f'''set -e; tar -xf /in/src.tar -C /repo && cd /repo && pnpm install --frozen-lockfile >&2
pnpm add -D --ignore-workspace-root-check @stryker-mutator/core @stryker-mutator/vitest-runner >&2 || pnpm add -D -w @stryker-mutator/core @stryker-mutator/vitest-runner >&2
# TypeScript 7 (native) lacks the JS API Stryker's tsconfig preprocessor needs; typecheck is irrelevant for mutant kills.
rm -f tsconfig.json
echo 'import {{ defineConfig }} from "vitest/config"; export default defineConfig({{ test: {{ include: ["test/**/*.test.ts"], exclude: {exc}.concat(["**/node_modules/**"]) }} }});' > vitest.stryker.config.mjs
cat > stryker.config.mjs <<'EOF2'
{CFG}
EOF2
mkdir -p /out; pnpm exec stryker run >&2 || true'''
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp); (tmp / "out").mkdir()
    subprocess.run(["git", "-C", str(repo), "archive", "-o", str(tmp / "src.tar"), sha], check=True)
    t0 = time.time()
    p = subprocess.run(["docker", "run", "--rm", "-v", f"{tmp}:/in", "-v", f"{tmp}/out:/out", "-v", "impactnet-pnpm-store:/root/.local/share/pnpm",
                        "-e", "CI=true", a.image, "bash", "-c", SCRIPT], capture_output=True, text=True)
    (pathlib.Path(a.out).with_suffix(".log")).write_text(p.stderr[-20000:])
    rep = json.loads((tmp / "out/report.json").read_text())
    tests = {t["id"]: f for f, fd in rep.get("testFiles", {}).items() for t in fd["tests"]}
    ms = []
    for f, fd in rep["files"].items():
        for m in fd["mutants"]:
            ms.append({"id": m["id"], "file": f, "mutator": m["mutatorName"], "line": m["location"]["start"]["line"], "col": m["location"]["start"]["column"],
                       "status": m["status"], "killed_by_files": sorted({tests[t] for t in m.get("killedBy", []) if t in tests}),
                       "covered_by_files": sorted({tests[t] for t in m.get("coveredBy", []) if t in tests})})
pathlib.Path(a.out).write_text(json.dumps({"commit": sha, "wall_s": round(time.time() - t0, 1), "mutants": ms}))
import collections; print(len(ms), "mutants", dict(collections.Counter(m["status"] for m in ms)), round(time.time() - t0), "s")
