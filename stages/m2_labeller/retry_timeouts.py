#!/usr/bin/env python3
"""Mutants whose batch run hit the 120s limit (status Error, secs>=100) are hangs, i.e. effectively killed, and dropping them would bias labels toward quiet failures.
Re-run each one file-by-file (45s per file; fail or timeout = failing, confirmed twice) and update the mutant JSON in place (status Killed/Survived, via=split-timeout).
Usage: retry_timeouts.py REPO MUTDIR [MUTDIR...]"""
import json, pathlib, subprocess, sys, tarfile, tempfile
H = pathlib.Path(__file__).resolve().parent; repo = sys.argv[1]
for md in sys.argv[2:]:
    for f in sorted(pathlib.Path(md).glob("*.json")):
        d = json.load(open(f)); bad = [m for m in d["mutants"] if m["status"] in ("Error", "Flaky") and m["secs"] >= 100 and not m.get("via")]
        if not bad: continue
        P = d["parent"]
        with tempfile.TemporaryDirectory() as wt:
            tar = pathlib.Path(wt) / "src.tar"
            subprocess.run(["git", "-C", repo, "archive", "-o", str(tar), P, "src"], check=True)
            with tarfile.open(tar) as tf:
                tf.extractall(wt, filter="data", members=[m for m in tf.getmembers() if not (m.issym() or m.islnk())])
            gm = {f"{x['file']}:{x['start']}:{x['mutator']}": x for x in json.loads(subprocess.run(["node", str(H / "gen_mutants.mjs"), wt, *sorted({m['file'] for m in bad})], capture_output=True, text=True, encoding="utf-8", errors="replace", check=True).stdout)}
        jobs = [{"id": m["id"], "file": m["file"], "start": gm[m["id"]]["start"], "end": gm[m["id"]]["end"], "replacement": m["replacement"], "tests": m["tests"], "split": True} for m in bad]
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp); (tmp / "out").mkdir()
            subprocess.run(["git", "-C", repo, "archive", "-o", str(tmp / "src.tar"), P], check=True)
            (tmp / "jobs.json").write_text(json.dumps(jobs)); (tmp / "run_mutants.mjs").write_text((H / "run_mutants.mjs").read_text())
            subprocess.run(["docker", "run", "--rm", "-v", f"{tmp}:/in", "-v", f"{tmp}/out:/out", "-v", "impactnet-pnpm-store:/root/.local/share/pnpm", "-e", "CI=true", "impactnet-node", "bash", "-c",
                            "tar -xf /in/src.tar -C /repo && cd /repo && pnpm install --frozen-lockfile >/dev/null 2>&1 && node /in/run_mutants.mjs /in/jobs.json /out/res.json"], capture_output=True)
            res = {x["id"]: x for x in json.loads((tmp / "out/res.json").read_text())}
        for m in bad:
            if m["id"] in res: m.update(status=res[m["id"]]["status"], killed_by_files=res[m["id"]]["killed_by_files"], via="split-timeout")
        json.dump(d, open(f, "w")); print("retried", P[:8], [(m["status"], len(m["killed_by_files"])) for m in bad], file=sys.stderr)
