#!/usr/bin/env python3
"""Overlap between B3-A's LLM ranking and B4's call-graph ranking inside the covering set.
Per >10-stratum killed mutant: top-5 set overlap, and whether the FAILING tests each finds in
its top-5 differ (complementarity -> stacking promise). Deterministic B4 (name tiebreak).
Usage: b3_b4_overlap.py ROWS.jsonl GRAPHS.db B3_A.jsonl"""
import collections, json, sqlite3, sys
rowsf, dbf, b3f = sys.argv[1:4]
rows = [json.loads(l) for l in open(rowsf)]
changes = collections.OrderedDict()
for r in rows: changes.setdefault(r["change_id"], []).append(r)
meta = {c: v[0] for c, v in changes.items()}
parents = sorted({m["parent"] for m in meta.values()})
con = sqlite3.connect(dbf)
B3 = {json.loads(l)["change_id"]: json.loads(l)["ranking"] for l in open(b3f)}

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
graphs = {P: G(P) for P in parents}; INF = 10**6

ov, found_same, found_comp, union_gain, vs10 = [], 0, 0, [], []
per_change = []
for c, rs in changes.items():
    if c not in B3: continue
    cov = [r["test_file"] for r in rs if r["covers"]]
    if len(cov) <= 10: continue
    fail = {r["test_file"] for r in rs if r["fails"]}
    if not fail: continue
    m = meta[c]; g = graphs[m["parent"]]
    imp = g.bfs(g.rimp, f"file:{m['src_file']}"); call = g.bfs(g.rcall, g.locate(m["src_file"], m["line"]))
    tdist = {}
    for n, d in call.items():
        f = g.nodes.get(n, (0, ""))[1]
        if f: tdist[f] = min(tdist.get(f, INF), d)
    b4 = sorted(cov, key=lambda t: (tdist.get(t, INF), imp.get(f"file:{t}", INF), t))
    b3 = [t for t in B3[c] if t in set(cov)]
    t5b3, t5b4 = set(b3[:5]), set(b4[:5])
    f5b3, f5b4 = t5b3 & fail, t5b4 & fail
    ov.append(len(t5b3 & t5b4) / 5)
    union = t5b3 | t5b4
    if f5b3 != f5b4: found_comp += 1
    else: found_same += 1
    union_gain.append(len(union & fail) - max(len(f5b3), len(f5b4)))
    # equal-budget check: union of the two top-5s (<=10 slots) vs each ranker's own top-10
    f10b3, f10b4 = set(b3[:10]) & fail, set(b4[:10]) & fail
    vs10.append(len(union & fail) - max(len(f10b3), len(f10b4)))
    per_change.append({"change": c, "top5_overlap": len(t5b3 & t5b4), "b3_found": sorted(f5b3), "b4_found": sorted(f5b4), "n_fail": len(fail)})
import statistics
print(json.dumps({"n_mutants": len(ov),
                  "mean_top5_overlap": round(statistics.mean(ov), 3),
                  "mutants_where_top5_fail_sets_differ": found_comp,
                  "mutants_where_identical": found_same,
                  "mean_extra_failing_found_by_union": round(statistics.mean(union_gain), 3),
                  "frac_mutants_union_finds_more": round(sum(u > 0 for u in union_gain) / len(union_gain), 3),
                  "equal_budget_union_vs_best_top10": round(statistics.mean(vs10), 3),
                  "frac_mutants_union_beats_best_top10": round(sum(u > 0 for u in vs10) / len(vs10), 3)}, indent=1))
json.dump(per_change, open("data/b3_b4_overlap_detail.json", "w"), indent=1)
