#!/usr/bin/env python3
"""Error analysis: for mutants where B4 ranks failing tests in the BOTTOM half of the covering
set, characterise the mutations and tests vs mutants where B4 succeeds.
Checks: call-graph reachability of failing tests, direct import, mock usage (vi/jest mock/spyOn),
dynamic import(), integration-suite membership, mutant fan-in, mutator type, lexical overlap.
Analysis only -- does not feed M1 features.
Usage: b4_misses.py ROWS.jsonl GRAPHS.db REPO [--min-cov 11]"""
import argparse, collections, json, math, re, sqlite3, statistics, subprocess, sys
ap = argparse.ArgumentParser(); ap.add_argument("rows"); ap.add_argument("db"); ap.add_argument("repo")
ap.add_argument("--min-cov", type=int, default=11)
a = ap.parse_args()
rows = [json.loads(l) for l in open(a.rows)]
changes = collections.OrderedDict()
for r in rows: changes.setdefault(r["change_id"], []).append(r)
meta = {c: v[0] for c, v in changes.items()}
con = sqlite3.connect(a.db)
git = lambda *x: subprocess.run(["git", "-C", a.repo, *x], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout

class G:
    def __init__(s, P):
        s.nodes = {i: (k, f, st, en) for i, k, f, st, en in con.execute("SELECT id,kind,file,start_line,end_line FROM nodes WHERE commit_hash=?", (P,))}
        s.rimp, s.rcall = collections.defaultdict(set), collections.defaultdict(set)
        for t, src, dst in con.execute("SELECT type,src,dst FROM edges WHERE commit_hash=? AND type IN ('imports','calls')", (P,)):
            (s.rimp if t == "imports" else s.rcall)[dst].add(src)
        s.by_file = collections.defaultdict(list)
        for i, (k, f, st, en) in s.nodes.items():
            if k == "function": s.by_file[f].append((en - st, st, en, i))
    def locate(s, f, line):
        c = [x for x in s.by_file.get(f, []) if x[1] <= line <= x[2]]
        return min(c)[3] if c else f"file:{f}"
    def bfs(s, adj, start):
        d, q = {start: 0}, collections.deque([start])
        while q:
            u = q.popleft()
            for v in adj.get(u, ()):
                if v not in d: d[v] = d[u] + 1; q.append(v)
        return d
graphs = {P: G(P) for P in {m["parent"] for m in meta.values()}}; INF = 10**6

MOCK = re.compile(r"(vi\.(mock|spyOn|fn)|jest\.(mock|spyOn|fn)|mockResolvedValue|mockImplementation)")
DYN = re.compile(r"await\s+import\s*\(|import\s*\(")
STOP = {"src", "test", "tests", "index", "ts", "d", "mts", "cts", "unit", "mod", "main"}
def toks(s):
    out = set()
    for piece in re.split(r"[^A-Za-z0-9]+", s):
        for t in re.findall(r"[A-Z]+(?![a-z])|[A-Z][a-z0-9]*|[a-z0-9]+", piece):
            t = t.lower()
            if t not in STOP: out.add(t)
    return out

testcache = {}
def tflags(P, t):
    if (P, t) not in testcache:
        src = git("show", f"{P}:{t}")
        testcache[(P, t)] = {"mock": bool(MOCK.search(src)), "dyn": bool(DYN.search(src)), "loc": len(src.splitlines())}
    return testcache[(P, t)]

out = []
for c, rs in changes.items():
    cov = [r for r in rs if r["covers"]]
    if len(cov) < a.min_cov or not any(r["fails"] for r in cov): continue
    m = meta[c]; P = m["parent"]; g = graphs[P]
    start = g.locate(m["src_file"], m["line"])
    call = g.bfs(g.rcall, start); imp = g.bfs(g.rimp, f"file:{m['src_file']}")
    tdist = {}
    for n, d in call.items():
        f = g.nodes.get(n, (0, ""))[1]
        if f: tdist[f] = min(tdist.get(f, INF), d)
    order = sorted((r["test_file"] for r in cov), key=lambda t: (tdist.get(t, INF), imp.get(f"file:{t}", INF), t))
    pos = {t: i for i, t in enumerate(order)}
    fails = [r["test_file"] for r in cov if r["fails"]]
    rel = sorted(pos[t] / max(len(order) - 1, 1) for t in fails)
    miss = sum(p >= 0.5 for p in rel) / len(rel) >= 0.5
    fl = [tflags(P, t) for t in fails]
    mt = toks(m["src_file"]) | (toks(start.split("#", 1)[1]) if "#" in start else set())
    rec = {"change": c[:24], "mutator": c.split(":")[-1], "src_file": m["src_file"], "miss": miss,
           "ncov": len(cov), "nfail": len(fails),
           "frac_fail_unreachable": sum(tdist.get(t, INF) == INF for t in fails) / len(fails),
           "frac_cov_unreachable": sum(tdist.get(t, INF) == INF for t in order) / len(order),
           "frac_fail_mock": sum(x["mock"] for x in fl) / len(fl),
           "frac_fail_dyn": sum(x["dyn"] for x in fl) / len(fl),
           "frac_fail_integration": sum("/tests/" in t or "tests/" in t.split("/")[1:2] for t in fails) / len(fails),
           "frac_fail_direct_import": sum(imp.get(f"file:{t}", INF) == 1 for t in fails) / len(fails),
           "mean_lex_fail": statistics.mean(len(mt & toks(t)) for t in fails),
           "fan_in": len(g.rcall.get(start, ())),
           "mut_src_dyn": bool(DYN.search(git("show", f"{P}:{m['src_file']}")))}
    out.append(rec)

misses = [r for r in out if r["miss"]]; hits = [r for r in out if not r["miss"]]
print(f"mutants analysed: {len(out)}  B4-miss: {len(misses)} ({100*len(misses)/len(out):.0f}%)  B4-hit: {len(hits)}")
def cmp(k):
    a_, b_ = [r[k] for r in misses], [r[k] for r in hits]
    return f"{statistics.mean(a_):.3f} vs {statistics.mean(b_):.3f}"
for k in ["frac_fail_unreachable", "frac_cov_unreachable", "frac_fail_mock", "frac_fail_dyn",
          "frac_fail_integration", "frac_fail_direct_import", "mean_lex_fail", "fan_in", "mut_src_dyn", "ncov", "nfail"]:
    print(f"  {k:26s} miss {cmp(k)}")
print("\nmiss by mutator:", dict(collections.Counter(r["mutator"] for r in misses)))
print("misses concentrated in files:", collections.Counter(r["src_file"] for r in misses).most_common(8))
print("\nworst misses (sample):")
for r in sorted(misses, key=lambda r: -r["nfail"])[:10]:
    print(f"  {r['change']}  {r['mutator']}  {r['src_file'][-50:]}  nfail={r['nfail']}/{r['ncov']} unreachable={r['frac_fail_unreachable']:.2f} mock={r['frac_fail_mock']:.2f} integ={r['frac_fail_integration']:.2f}")
