#!/usr/bin/env python3
"""Run the M1 extractor at every parent commit in MUTDIR; all graphs go into one SQLite (rows carry commit_hash).
Usage: extract_graphs.py REPO MUTDIR OUT.db"""
import json, pathlib, subprocess, sys, tarfile, tempfile
repo, mutdir, db = sys.argv[1:4]; M1 = pathlib.Path(__file__).resolve().parents[1] / "m1_extractor"
for f in sorted(pathlib.Path(mutdir).glob("*.json")):
    P = json.load(open(f)).get("parent")
    if not P: continue
    with tempfile.TemporaryDirectory() as wt:
        tar = pathlib.Path(wt) / "a.tar"
        subprocess.run(["git", "-C", repo, "archive", "-o", str(tar), P], check=True)
        with tarfile.open(tar) as tf:
            tf.extractall(wt, filter="data", members=[m for m in tf.getmembers() if not (m.issym() or m.islnk())])
        g = subprocess.run(["node", str(M1 / "extract.mjs"), wt, P], capture_output=True, text=True, encoding="utf-8", errors="replace", check=True).stdout
        (pathlib.Path(wt) / "g.json").write_text(g)
        subprocess.run([sys.executable, str(M1 / "build_db.py"), str(pathlib.Path(wt) / "g.json"), db], check=True)
