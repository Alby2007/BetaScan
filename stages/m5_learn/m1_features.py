#!/usr/bin/env python3
"""M1 feature builder: per (mutant, covering-test) pair, repo-agnostic features.
Graph semantics identical to m3_baselines/evaluate.py (reverse-call BFS from the mutated function,
reverse-import BFS from the mutated file, lexical token overlap, coverage counts from cov_P).
Usage: m1_features.py ROWS.jsonl GRAPHS.db --m2dir DIR[,DIR...] --out features.jsonl [--b3dir DIR]"""
import argparse, collections, glob, json, math, os, re, sqlite3
ap = argparse.ArgumentParser(); ap.add_argument("rows"); ap.add_argument("db"); ap.add_argument("out")
ap.add_argument("--m2dir", required=True); ap.add_argument("--b3dir", default="")
a = ap.parse_args()

rows = [json.loads(l) for l in open(a.rows)]
changes = collections.OrderedDict()
for r in rows: changes.setdefault(r["change_id"], []).append(r)
meta = {c: v[0] for c, v in changes.items()}
parents = sorted({m["parent"] for m in meta.values()})
con = sqlite3.connect(a.db)

covmaps, covsize = {}, {}
for f in [g for d in a.m2dir.split(",") for g in glob.glob(os.path.join(d, "[0-9a-f]*.json"))]:
    r = json.load(open(f))
    tests = r.get("cov_P", {}).get("tests", {})
    covmaps[r["parent"]] = {t: v.get("covered", {}) for t, v in tests.items()}
    covsize[r["parent"]] = {t: sum(len(l) for l in v.get("covered", {}).values()) for t, v in tests.items()}

B3 = {}
if a.b3dir:
    for f in glob.glob(a.b3dir + "/b3_*.jsonl"):
        for l in open(f):
            j = json.loads(l); B3.setdefault(j["variant"], {})[j["change_id"]] = {t: i for i, t in enumerate(j["ranking"])}

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

STOP_TOK = {"src", "test", "tests", "index", "ts", "d", "mts", "cts", "unit", "mod", "main"}
def toks(s):
    out = set()
    for piece in re.split(r"[^A-Za-z0-9]+", s):
        for t in re.findall(r"[A-Z]+(?![a-z])|[A-Z][a-z0-9]*|[a-z0-9]+", piece):
            t = t.lower()
            if t not in STOP_TOK: out.add(t)
    return out

feats = []
for c, rs in changes.items():
    m = meta[c]; P = m["parent"]; g = graphs[P]
    covt = [r["test_file"] for r in rs if r["covers"]]
    if not covt or not any(r["fails"] for r in rs): continue
    start = g.locate(m["src_file"], m["line"])
    call = g.bfs(g.rcall, start); imp = g.bfs(g.rimp, f"file:{m['src_file']}")
    tdist = {}
    for n, d in call.items():
        f = g.nodes.get(n, (0, ""))[1]
        if f: tdist[f] = min(tdist.get(f, INF), d)
    mt = toks(m["src_file"]) | (toks(start.split("#", 1)[1]) if "#" in start else set())
    fan_in = len(g.rcall.get(start, ()))
    csz = covsize.get(P, {}); cmaps = covmaps.get(P, {})
    mx = max((csz.get(t, 0) for t in covt), default=1) or 1
    b3a = B3.get("A", {}).get(c)
    for r in rs:
        t = r["test_file"]
        if not r["covers"]: continue
        ov = mt & toks(t); tgt = len(cmaps.get(t, {}).get(m["src_file"], [])); tot = csz.get(t, 0)
        feats.append({"change": c, "test": t, "src_file": m["src_file"], "parent": P,
                      "label": int(r["fails"]), "ncov": len(covt), "dur_ms": r.get("dur_ms", 0),
                      "f": {"call_dist": min(tdist.get(t, INF), 9),
                            "imp_dist": min(imp.get(f"file:{t}", INF), 9),
                            "direct_import": float(imp.get(f"file:{t}", INF) == 1),
                            "lex_overlap": float(len(ov)),
                            "lex_jaccard": len(ov) / len(mt | toks(t)),
                            "log_covsize": math.log1p(tot),
                            "covsize_rel": tot / mx,
                            "targeted_lines": float(tgt),
                            "targeted_rel": tgt / tot if tot else 0.0,
                            "fan_in_mut": float(fan_in),
                            "log_dur": math.log1p(r.get("dur_ms", 0)),
                            "log_ncov": math.log1p(len(covt)),
                            "has_b3": float(b3a is not None),
                            "b3_rank": float(b3a.get(t, 99)) if b3a else math.nan}})
out = open(a.out, "w")
for x in feats: out.write(json.dumps(x) + "\n")
print(len(feats), "pairs;", len({x["change"] for x in feats}), "mutants;", len({x["src_file"] for x in feats}), "src files")
