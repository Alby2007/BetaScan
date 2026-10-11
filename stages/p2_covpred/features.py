#!/usr/bin/env python3
"""Feature builder for the coverage-prediction learner (P3 spec, exploratory on h3).
Per (test, function) pair emits repo-agnostic structural features. Raw values here;
within-test rank/percentile normalisation is applied inside cv.py per fold so no
information crosses the boundary. No identity features: snap/test/func emitted only
as grouping keys for CV and evaluation, never as model inputs.
Usage: features.py PAIRS.jsonl[.gz] SIGNALS.jsonl DB REPO OUT.npz"""
import argparse, collections, gzip, json, os, re, sqlite3, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from impclass import imp_specs, git_show, resolve, bfs, toks, runtime_adj, pkgdirs, imp_dist
import numpy as np
ap = argparse.ArgumentParser()
for x in ["pairs", "signals", "db", "repo", "out"]: ap.add_argument(x)
a = ap.parse_args()
INF = 10**6
con = sqlite3.connect(a.db)
op = gzip.open if a.pairs.endswith(".gz") else open
pairs = [json.loads(l) for l in op(a.pairs, "rt")]
sigs = {}
for l in open(a.signals):
    d = json.loads(l); sigs[(d["parent"], d["test"])] = d
by_test = collections.defaultdict(list)
for p in pairs: by_test[(p["snapshot"], p["test"])].append(p)
by_snap = collections.defaultdict(list)
for (P, t), rows in by_test.items(): by_snap[P].append((t, rows))

FEATS = ["impd", "imp_direct", "imp_trans", "typeonly_reach", "dyn_hit", "mock_hit",
         "barrel_depth", "calld", "name_in_test", "exports_hit_frac", "path_overlap",
         "tok_overlap", "same_basename", "dir_dist", "func_size", "file_size",
         "fan_in", "fan_out"]
X = {k: [] for k in FEATS}; Y = []; G_snap = []; G_test = []; G_file = []
for P, test_rows in by_snap.items():
    call = collections.defaultdict(set); files = set(); fnodes = collections.defaultdict(list)
    finfo = {}; exports = collections.defaultdict(set); fsize = {}
    for i, k, f, s, e, ex in con.execute("SELECT id,kind,file,start_line,end_line,exported FROM nodes WHERE commit_hash=?", (P,)):
        files.add(f)
        if k == "function": fnodes[f].append(i); finfo[i] = (f, s, e)
        if ex and k in ("function", "class", "type", "variable"): exports[f].add(i.split("#")[-1].split("@")[0])
    for ty, src, dst in con.execute("SELECT type,src,dst FROM edges WHERE commit_hash=? AND type IN ('calls','defined_in')", (P,)):
        if ty == "calls": call[src].add(dst)
    fan_in = collections.Counter(); fan_out = collections.Counter()
    for s, d in con.execute("SELECT src,dst FROM edges WHERE commit_hash=? AND type IN ('calls','uses_type','imports')", (P,)):
        fan_out[s] += 1; fan_in[d] += 1
    for f, fns in fnodes.items():
        es = [finfo[i][2] for i in fns if i in finfo]
        if es: fsize[f] = max(es)
    for t, rows in test_rows: files |= {r["file"] for r in rows} | {t}
    rt, full_imp = runtime_adj(con, a.repo, P, files)
    pkg = pkgdirs(a.repo, P)
    print(f"snapshot {P}: {len(test_rows)} tests", flush=True)
    for t, rows in test_rows:
        idist = imp_dist(rt, t, pkg, files)
        full_clo = {x[5:] for x in bfs(full_imp, f"file:{t}") if x.startswith("file:")}
        sig = sigs.get((P, t), {})
        dyn = {resolve(m, t, files) for m in sig.get("dyn", [])}
        mocks = set()
        for m in sig.get("mocks", []):
            if not m.startswith("module:"):
                stem = m
                for cand in (stem + ".ts", stem + ".tsx", stem + "/index.ts", stem + "/index.tsx"):
                    if cand in files: stem = cand; break
                mocks.add(stem)
        cdist = {}
        for s in [f"file:{t}"] + fnodes.get(t, []):
            for n, dd in bfs(call, s).items():
                if dd < cdist.get(n, INF): cdist[n] = dd
        tsrc = git_show(a.repo, P, t); tidents = toks(tsrc); tt = toks(t)
        tbase = t.rsplit("/", 1)[-1].split(".")[0]
        for r in rows:
            fid = r["func"]; ff = r["file"]
            f_, s_, e_ = finfo.get(fid, (ff, 0, 0))
            fname = fid.split("#", 1)[1].split("@")[0] if "#" in fid else ""
            impd = min(idist.get(f"file:{ff}", INF), 9)
            fbase = ff.rsplit("/", 1)[-1].split(".")[0]
            dpath = ff.rsplit("/", 1)[0].split("/"); tpath = t.rsplit("/", 1)[0].split("/")
            common = 0
            for x, y_ in zip(dpath, tpath):
                if x == y_: common += 1
                else: break
            ddist = len(dpath) + len(tpath) - 2 * common
            vals = {
                "impd": impd,
                "imp_direct": float(impd == 1), "imp_trans": float(1 < impd < 9),
                "typeonly_reach": float(impd >= 9 and ff in full_clo),
                "dyn_hit": float(ff in dyn), "mock_hit": float(ff in mocks),
                "barrel_depth": float(ff.rsplit("/", 1)[-1].startswith("index.")),
                "calld": min(cdist.get(fid, INF), 9),
                "name_in_test": float(bool(fname) and fname.lower() in tidents),
                "exports_hit_frac": len(exports.get(ff, set()) & tidents) / max(1, len(exports.get(ff, set()))),
                "path_overlap": float(len(set(dpath) & set(tpath))),
                "tok_overlap": float(len(tt & (toks(ff) | toks(fname)))),
                "same_basename": float(tbase == fbase),
                "dir_dist": float(ddist),
                "func_size": float(e_ - s_ + 1), "file_size": float(fsize.get(ff, 0)),
                "fan_in": float(fan_in.get(fid, 0)), "fan_out": float(fan_out.get(fid, 0)),
            }
            for k, v in vals.items(): X[k].append(v)
            Y.append(r["covered"]); G_snap.append(P); G_test.append(f"{P}:{t}"); G_file.append(f"{P}:{ff}")
Xa = {k: np.array(v, dtype=np.float32) for k, v in X.items()}
np.savez_compressed(a.out, y=np.array(Y, dtype=np.int8), snap=np.array(G_snap), test=np.array(G_test), gfile=np.array(G_file), feats=list(FEATS), **{f"f_{k}": v for k, v in Xa.items()})
print("wrote", a.out, len(Y), "pairs x", len(FEATS), "features")
