#!/usr/bin/env python3
"""Verify stored trpc mutants against regeneration on the current machine.
Regenerates each parent's mutant set with gen_mutants.mjs and checks that every stored mutant's
id exists and that file/line/mutator/original/replacement match byte-for-byte. Reports which
mutants no longer regenerate (e.g. ts-morph version drift) and any field mismatches.
Usage: verify_mutants.py REPO OUTDIR"""
import collections, json, pathlib, subprocess, sys, tarfile, tempfile

H = pathlib.Path(__file__).resolve().parent
GEN = H.parent / "gen_mutants.mjs"
repo, outdir = pathlib.Path(sys.argv[1]).resolve(), pathlib.Path(sys.argv[2])

recs = []
for f in sorted(outdir.glob("[0-9a-f]*.json")):
    j = json.load(open(f))
    if "parent" in j and "mutants" in j: recs.append(j)

gen = {}
def regen(P, files):
    if P in gen: return gen[P]
    with tempfile.TemporaryDirectory() as wt:
        tar = pathlib.Path(wt) / "src.tar"
        subprocess.run(["git", "-C", str(repo), "archive", "-o", str(tar), P, "packages"], check=True)
        with tarfile.open(tar) as tf:
            tf.extractall(wt, filter="data", members=[m for m in tf.getmembers() if not (m.issym() or m.islnk())])
        r = subprocess.run(["node", str(GEN), wt, *files], capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)
        gen[P] = {f"{x['file']}:{x['start']}:{x['mutator']}": x for x in json.loads(r.stdout)}
        return gen[P]

tot = collections.Counter(); report = {"ok": [], "mismatch": [], "not_regenerable": []}
for rec in recs:
    P, commit = rec["parent"], rec["commit"][:8]
    files = sorted({m["file"] for m in rec["mutants"]})
    g = regen(P, files)
    st = collections.Counter()
    for m in rec["mutants"]:
        e = {"commit": commit, "id": m["id"], "line": m["line"], "n_tests": len(m.get("tests", [])), "status": m.get("status")}
        g0 = g.get(m["id"])
        if g0 is None: st["not_regenerable"] += 1; report["not_regenerable"].append(e); continue
        bad = [k for k in ("file", "line", "mutator", "original", "replacement") if g0.get(k) != m.get(k)]
        if bad: st["mismatch"] += 1; report["mismatch"].append({**e, "fields": bad}); continue
        st["ok"] += 1; report["ok"].append(e)
    tot.update(st)
    print(commit, dict(st), file=sys.stderr)
print(json.dumps({"totals": dict(tot), **{k: v for k, v in report.items() if k != "ok"}}, indent=1))
