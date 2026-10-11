#!/usr/bin/env python3
"""P1 heuristic baselines for coverage prediction: score (test,function) pairs and report AP.
C0 random | C1 runtime import closure (excl type-only + vi.mock'd) | C2 import distance |
C3 forward call-graph reachability | C4 lexical overlap | C5 lexicographic combo (impd, calld, lex)
Metrics: pooled AP, per-test macro AP, precision@{0.5,0.8} recall.
Usage: heuristics.py PAIRS.jsonl[.gz] SIGNALS.jsonl DB REPO --out report.md"""
import argparse, collections, gzip, json, random, re, sqlite3, subprocess
import numpy as np
ap = argparse.ArgumentParser(); ap.add_argument("pairs"); ap.add_argument("signals"); ap.add_argument("db"); ap.add_argument("repo")
ap.add_argument("--rows", default=""); ap.add_argument("--out", default="")
a = ap.parse_args()

op = gzip.open if a.pairs.endswith(".gz") else open
pairs = [json.loads(l) for l in op(a.pairs, "rt")]
con = sqlite3.connect(a.db)

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from impclass import imp_specs

def git_show(P, f):
    return subprocess.run(["git", "-C", a.repo, "show", f"{P}:{f}"], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
def resolve(spec, frm, files=()):
    if not spec.startswith("."): return "module:" + (spec if spec.startswith("node:") else "/".join(spec.split("/")[:2]) if spec.startswith("@") else spec.split("/")[0])
    base = frm.rsplit("/", 1)[0]; out = []
    for p in (base + "/" + spec).split("/"):
        if p == "..": out = out[:-1]
        elif p != ".": out.append(p)
    stem = "/".join(out)
    for cand in (stem + ".ts", stem + ".tsx", stem + "/index.ts", stem + "/index.tsx"):
        if cand in files: return cand
    return stem

sigs = collections.defaultdict(dict)
for l in open(a.signals):
    d = json.loads(l); sigs[(d["parent"], d["test"])] = d

STOP = {"src", "test", "tests", "index", "ts", "d", "mts", "cts", "unit", "mod", "main"}
def toks(s):
    out = set()
    for piece in re.split(r"[^A-Za-z0-9]+", s):
        for t in re.findall(r"[A-Z]+(?![a-z])|[A-Z][a-z0-9]*|[a-z0-9]+", piece):
            t = t.lower()
            if t not in STOP: out.add(t)
    return out

def bfs(adj, start):
    d, q = {start: 0}, collections.deque([start])
    while q:
        u = q.popleft()
        for v in adj.get(u, ()):
            if v not in d: d[v] = d[u] + 1; q.append(v)
    return d

INF = 10**6
HEU = ["C0", "C1", "C2", "C3", "C4", "C5"]
Y = {k: [] for k in HEU}; S = {k: [] for k in HEU}
# memory-lean grouping: group key -> flat list of ROW INDICES into Y/S
idx_test = collections.defaultdict(list); idx_func = collections.defaultdict(list); idx_snap = collections.defaultdict(list)
by_test = collections.defaultdict(list)
for p in pairs: by_test[(p["snapshot"], p["test"])].append(p)
by_snap = collections.defaultdict(list)
for (P, t), rows in by_test.items(): by_snap[P].append((t, rows))
snap_pos = {P: sum(x["covered"] for _, rs in rs_ for x in rs) / max(1, sum(len(rs) for _, rs in rs_)) for P, rs_ in by_snap.items()}
# mutation-target functions (optional --rows rows.jsonl): func ranges containing a mutant line
mut_funcs = set()
if a.rows:
    pf = {}
    for l in open(a.rows):
        r = json.loads(l); P0, f0, ln = r["parent"], r["src_file"], r["line"]
        if (P0, f0) not in pf:
            pf[(P0, f0)] = [(s, e, i) for s, e, i in con.execute(
                "SELECT start_line,end_line,id FROM nodes WHERE commit_hash=? AND kind='function' AND file=?", (P0, f0))]
        for s, e, i in pf[(P0, f0)]:
            if s <= ln <= e: mut_funcs.add(i)

rng = random.Random(0)
for P, test_rows in by_snap.items():
    imp = collections.defaultdict(set); call = collections.defaultdict(set); files = set()
    for ty, src, dst in con.execute("SELECT type,src,dst FROM edges WHERE commit_hash=? AND type IN ('imports','calls')", (P,)):
        (imp if ty == "imports" else call)[src].add(dst)
        if src.startswith("file:"): files.add(src[5:])
    for t, rows in test_rows: files |= {r["file"] for r in rows} | {t}
    typeonly = {}
    for f in files:
        run_specs, typ_specs = imp_specs(git_show(P, f))
        tg = {resolve(m, f, files) for m in typ_specs} - {resolve(m, f, files) for m in run_specs}
        if tg: typeonly[f] = tg
    imp_rt = collections.defaultdict(set)
    for src, ds in imp.items():
        for d in ds:
            if d[5:] not in typeonly.get(src[5:], ()): imp_rt[src].add(d)
    fnodes = collections.defaultdict(list)
    for i, k, f in con.execute("SELECT id,kind,file FROM nodes WHERE commit_hash=?", (P,)):
        if k == "function": fnodes[f].append(i)
    # workspace packages: in-repo package.json name -> dir; a module:X edge to a
    # workspace package exposes all files under its dir at distance+1 (ts-morph may
    # resolve the import via package exports instead of the workspace source)
    pkgdir = {}
    for pj in subprocess.run(["git", "-C", a.repo, "ls-tree", "-r", "--name-only", P], capture_output=True, text=True).stdout.splitlines():
        if pj.endswith("package.json") and pj.count("/") <= 3 and "node_modules" not in pj:
            try: nm = json.loads(git_show(P, pj)).get("name")
            except Exception: nm = None
            if nm and "/" in pj: pkgdir[nm] = pj.rsplit("/", 1)[0]
    print(f"snapshot {P}: {len(test_rows)} tests, {len(files)} files, {len(pkgdir)} pkgs", flush=True)
    for t, rows in test_rows:
        idist = bfs(imp_rt, f"file:{t}")
        # dynamic import() edges are not in the graph (extractor walks declarations
        # only); signals sidecar has per-test specs — treat as runtime edges at d=1+
        for m in sigs.get((P, t), {}).get("dyn", []):
            if m in files:
                for n, dd in bfs(imp_rt, f"file:{m}").items():
                    if dd + 1 < idist.get(n, INF): idist[n] = dd + 1
        for n, d in list(idist.items()):
            if n.startswith("module:") and n[7:] in pkgdir:
                dd = pkgdir[n[7:]] + "/"
                for f in files:
                    if f.startswith(dd) and d + 1 < idist.get(f"file:{f}", INF): idist[f"file:{f}"] = d + 1
        mocked = set()
        for m in sigs.get((P, t), {}).get("mocks", []):
            if not m.startswith("module:"):
                stem = m
                for cand in (stem + ".ts", stem + ".tsx", stem + "/index.ts", stem + "/index.tsx"):
                    if cand in files: stem = cand; break
                mocked.add(stem)
        starts = [f"file:{t}"] + fnodes.get(t, [])
        cdist = {}
        for s in starts:
            for n, dd in bfs(call, s).items():
                if dd < cdist.get(n, INF): cdist[n] = dd
        tt = toks(t)
        for r in rows:
            fid = r["func"]; ff = r["file"]; y = r["covered"]
            ft = toks(ff) | (toks(fid.split("#", 1)[1]) if "#" in fid else set())
            impd = min(idist.get(f"file:{ff}", INF), 9)
            cal = min(cdist.get(fid, INF), 9)
            clo = 1.0 if (idist.get(f"file:{ff}", INF) < INF and ff not in mocked) else 0.0
            lex = float(len(tt & ft))
            ri = len(Y["C0"])
            idx_test[(P, t)].append(ri); idx_func[(P, fid)].append(ri); idx_snap[P].append(ri)
            for k, v in [("C0", rng.random()), ("C1", clo), ("C2", -impd), ("C3", -cal),
                         ("C4", lex), ("C5", -10 * impd - cal + 0.01 * lex)]:
                Y[k].append(y); S[k].append(v)

from sklearn.metrics import average_precision_score, precision_recall_curve
def AP(y, s): return average_precision_score(y, s) if any(y) else float("nan")
def pat_recall(y, s, rt):
    pr, rc, _ = precision_recall_curve(y, s)
    ok = pr[rc >= rt]
    return float(ok.max()) if len(ok) else float("nan")

lines = ["# P1 heuristic baselines — coverage prediction\n",
         "C5 is a FIXED lexicographic formula `-10*impd - calld + 0.01*lex` — no fitting on labels (not in-sample).\n",
         "| ranker | pooled AP | snap-macro AP | per-test AP | per-func AP | per-func AP (mutants) | P@R50 | P@R80 |",
         "|---|---|---|---|---|---|---|---|"]
def grp(ix, y, s):
    return AP([y[i] for i in ix], [s[i] for i in ix]) if any(y[i] for i in ix) else float("nan")
for k in HEU:
    y = np.array(Y[k]); s = np.array(S[k], dtype=float)
    yl, sl = Y[k], S[k]
    pt = [grp(ix, yl, sl) for ix in idx_test.values()]
    pf = [grp(ix, yl, sl) for ix in idx_func.values()]
    pfm = [grp(ix, yl, sl) for (P, fid), ix in idx_func.items() if fid in mut_funcs]
    ps = [grp(ix, yl, sl) for ix in idx_snap.values()]
    pt = [v for v in pt if v == v]; pf = [v for v in pf if v == v]; pfm = [v for v in pfm if v == v]; ps = [v for v in ps if v == v]
    lines.append(f"| {k} | {AP(y, s):.3f} | {np.mean(ps):.3f} | {np.mean(pt):.3f} | {np.mean(pf):.3f} | {np.mean(pfm) if pfm else float('nan'):.3f} | {pat_recall(y, s, .5):.3f} | {pat_recall(y, s, .8):.3f} |")
lines.append("\n## era bands (snap-macro AP by snapshot positive rate)\n")
bands = sorted({("low" if snap_pos[P] < .3 else "high") for P in snap_pos})
lines.append("| ranker | " + " | ".join(f"pos{b} n={sum(1 for P in snap_pos if (snap_pos[P]<.3)==(b=='low'))}" for b in bands) + " |")
lines.append("|---|" + "---|" * len(bands))
for k in HEU:
    cells = []
    for b in bands:
        vals = [grp(idx_snap[P], Y[k], S[k]) for P in snap_pos if (snap_pos[P] < .3) == (b == "low")]
        cells.append(f"{np.mean(vals):.3f}" if vals else "-")
    lines.append(f"| {k} | " + " | ".join(cells) + " |")
rep = "\n".join(lines) + "\n"
print(rep)
if a.out: open(a.out, "w", encoding="utf-8").write(rep)
