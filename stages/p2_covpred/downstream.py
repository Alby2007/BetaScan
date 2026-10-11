#!/usr/bin/env python3
"""Downstream preview: rank ALL green tests for each killed mutant by fixed C2 / C5
scores (no fitting) and report full-suite n95 + n95_vs_B5, vs the B4/B5a numbers
already on record for the same rows. Same seed protocol as evaluate.py (3 seeds,
rng key f"{change_id}{seed}").
Usage: downstream.py ROWS.jsonl DB REPO --stratum 10 --out rep.md"""
import argparse, collections, json, math, random, re, sqlite3, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from impclass import git_show, resolve, bfs, toks, runtime_adj, pkgdirs, imp_dist
ap = argparse.ArgumentParser(); ap.add_argument("rows"); ap.add_argument("db"); ap.add_argument("repo")
ap.add_argument("--stratum", type=int, default=10); ap.add_argument("--out", default="")
a = ap.parse_args()
INF = 10**6; isTest = re.compile(r"\.(test|spec)\.[cm]?[tj]sx?$")
con = sqlite3.connect(a.db)

changes = collections.defaultdict(list); meta = {}
for l in open(a.rows):
    r = json.loads(l)
    changes[r["change_id"]].append(r); meta[r["change_id"]] = r

# per-parent graph context
ctx = {}
def graph_ctx(P):
    if P not in ctx:
        fnodes = collections.defaultdict(list); files = set()
        frange = collections.defaultdict(list)
        for i, k, f, s, e in con.execute("SELECT id,kind,file,start_line,end_line FROM nodes WHERE commit_hash=?", (P,)):
            files.add(f)
            if k == "function": fnodes[f].append(i); frange[f].append((s, e, i))
        call = collections.defaultdict(set)
        for s, d in con.execute("SELECT src,dst FROM edges WHERE commit_hash=? AND type='calls'", (P,)):
            call[s].add(d)
        rt, _ = runtime_adj(con, a.repo, P, files)
        ctx[P] = (fnodes, files, frange, call, rt, pkgdirs(a.repo, P))
    return ctx[P]

def func_at(frange, f, line):
    for s, e, i in frange.get(f, ()):
        if s <= line <= e: return i
    return None

def n95(scores, rows, c):
    """full-suite n95 + n95_vs_B5 averaged over 3 seeds, evaluate.py semantics."""
    rb = {r["test_file"]: r for r in rows}
    m = sum(r["fails"] for r in rows); ncov = sum(r["covers"] for r in rows)
    need = math.ceil(.95 * m)
    if m == 0: return None, None
    outs = []
    for s in range(3):
        rng = random.Random(f"{c}{s}")
        order = sorted(rb, key=lambda t: (-scores[t], rng.random()))
        seen = 0
        for i, t in enumerate(order):
            seen += rb[t]["fails"]
            if seen >= need: outs.append((i + 1, (i + 1) / ncov)); break
    if not outs: return None, None
    return sum(x[0] for x in outs) / len(outs), sum(x[1] for x in outs) / len(outs)

idist_c = cdist_c = {}
res = collections.defaultdict(list)
for c, rows in changes.items():
    m = meta[c]; P = m["parent"]; sf = m["src_file"]
    fnodes, files, frange, call, rt, pkg = graph_ctx(P)
    fid = func_at(frange, sf, m["line"])
    scores = {"C2": {}, "C5": {}, "C5b": {}}
    tests = [r["test_file"] for r in rows]
    for t in tests:
        if (P, t) not in idist_c:
            idist_c[(P, t)] = imp_dist(rt, t, pkg, files)
        idist = idist_c[(P, t)]
        if (P, t) not in cdist_c:
            cd = {}
            for s0 in [f"file:{t}"] + fnodes.get(t, []):
                for n, dd in bfs(call, s0).items():
                    if dd < cd.get(n, INF): cd[n] = dd
            cdist_c[(P, t)] = cd
        cd = cdist_c[(P, t)]
        impd = min(idist.get(f"file:{sf}", INF), 9)
        cal = min(cd.get(fid, INF), 9) if fid else 9
        lex = float(len(toks(t) & (toks(sf) | (toks(fid.split("#", 1)[1]) if fid and "#" in fid else set()))))
        scores["C2"][t] = -impd
        scores["C5"][t] = -10 * impd - cal + 0.01 * lex
        scores["C5b"][t] = -10 * cal - impd + 0.01 * lex   # B4 ordering: call first
    ncov = sum(r["covers"] for r in rows)
    band = ">10" if ncov > a.stratum else "<=10"
    for k in scores:
        a95, rel = n95(scores[k], rows, c)
        if a95 is not None: res[(k, band)].append((a95, rel))

lines = ["# Downstream preview — fixed C2/C5 ranking of tests for killed mutants\n",
         "| ranker | stratum | n mutants | mean n95 | mean n95_vs_B5 |", "|---|---|---|---|---|"]
for (k, band), xs in sorted(res.items()):
    lines.append(f"| {k} | {band} | {len(xs)} | {sum(x[0] for x in xs)/len(xs):.2f} | {sum(x[1] for x in xs)/len(xs):.3f} |")
rep = "\n".join(lines) + "\n"
print(rep)
if a.out: open(a.out, "w", encoding="utf-8").write(rep)
