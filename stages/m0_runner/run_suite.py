#!/usr/bin/env python3
"""Run a repo's Vitest suite in Docker and emit per-test-file pass/fail JSON.

Usage: run_suite.py REPO_DIR [--commit SHA] [--out out.json] [--image impactnet-node]
The repo is copied to a scratch dir (via git worktree-free `git archive`) so the
original checkout is never mutated.
"""
import argparse, json, subprocess, sys, tempfile, time, pathlib

def sh(cmd, **kw):
    return subprocess.run(cmd, check=True, text=True, **kw)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--commit", default="HEAD")
    ap.add_argument("--out", default="-")
    ap.add_argument("--image", default="impactnet-node")
    ap.add_argument("--install", default="pnpm install --frozen-lockfile")
    ap.add_argument("--test", default="pnpm exec vitest --run --reporter=json --outputFile=/tmp/vitest.json")
    a = ap.parse_args()
    repo = pathlib.Path(a.repo).resolve()
    sha = sh(["git", "-C", str(repo), "rev-parse", a.commit], capture_output=True).stdout.strip()
    with tempfile.TemporaryDirectory() as tmp:
        tar = pathlib.Path(tmp) / "src.tar"
        sh(["git", "-C", str(repo), "archive", "-o", str(tar), sha])
        script = f"tar -xf /in/src.tar -C /repo && cd /repo && {a.install} >&2 && ({a.test} >&2 || true) && cat /tmp/vitest.json"
        t0 = time.time()
        p = subprocess.run(["docker", "run", "--rm", "-v", f"{tmp}:/in:ro", "-v", "impactnet-pnpm-store:/root/.local/share/pnpm",
                            "-e", "CI=true", a.image, "bash", "-c", script], text=True, capture_output=True)
        sys.stderr.write(p.stderr[-3000:])
        if p.returncode: sys.exit(p.returncode)
    raw = json.loads(p.stdout[p.stdout.index("{"):])
    files = {}
    for f in raw["testResults"]:
        name = f["name"].removeprefix("/repo/")
        st = {"passed": "pass", "failed": "fail"}.get(f["status"], f["status"])
        files[name] = {"status": st, "tests": len(f["assertionResults"]),
                       "failed": sum(t["status"] == "failed" for t in f["assertionResults"]),
                       "duration_ms": round(f["endTime"] - f["startTime"])}
    res = {"commit": sha, "wall_s": round(time.time() - t0, 1), "files": files}
    s = json.dumps(res, indent=1)
    (sys.stdout if a.out == "-" else open(a.out, "w")).write(s + "\n")

if __name__ == "__main__":
    main()
