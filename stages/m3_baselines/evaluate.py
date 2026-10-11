#!/usr/bin/env python3
"""M3: baselines B0,B1,B2,B4 (+ extra B5 coverage) and the evaluator.
Usage: evaluate.py MUTANT_ROWS.jsonl GRAPHS.db OUT_PREFIX [--test-parents 4] [--seeds 5]
Everything a ranker sees comes from the parent commit P (graph at P, coverage at P, training history from EARLIER parents only)."""
import argparse, collections, json, math, os, random, sqlite3, statistics, sys
ap = argparse.ArgumentParser(); ap.add_argument("rows"); ap.add_argument("db"); ap.add_argument("out")
ap.add_argument("--m2dir", default="data/m2"); ap.add_argument("--test-parents", type=int, default=4); ap.add_argument("--seeds", type=int, default=5)
ap.add_argument("--b3dir", default="data/b3")
a = ap.parse_args()
rows = [json.loads(l) for l in open(a.rows)]
changes = collections.OrderedDict()
for r in rows: changes.setdefault(r["change_id"], []).append(r)
meta = {c: v[0] for c, v in changes.items()}
parents = sorted({m["parent"] for m in meta.values()}, key=lambda p: next(m["date"] for m in meta.values() if m["parent"] == p))
test_parents, train_parents = set(parents[-a.test_parents:]), set(parents[:-a.test_parents])
con = sqlite3.connect(a.db)
import glob
covsize = {}
for f in [g for d in a.m2dir.split(",") for g in glob.glob(os.path.join(d, "[0-9a-f]*.json"))]:
    r = json.load(open(f)); covsize[r["parent"]] = {t: sum(len(l) for l in v["covered"].values()) for t, v in r.get("cov_P", {}).get("tests", {}).items()}

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
graphs = {P: G(P) for P in parents}
INF = 10**6

def hist_model(train_changes):
    fa, da, gl = collections.Counter(), collections.Counter(), collections.Counter()
    fn, dn = collections.Counter(), collections.Counter(); tn = 0
    for c in train_changes:
        m = meta[c]; f = m["src_file"]; d = os.path.dirname(f); fn[f] += 1; dn[d] += 1; tn += 1
        for r in changes[c]:
            if r["fails"]: fa[(f, r["test_file"])] += 1; da[(d, r["test_file"])] += 1; gl[r["test_file"]] += 1
    def key(m, t):
        f = m["src_file"]; d = os.path.dirname(f)
        return (-(fa[(f, t)] / fn[f] if fn[f] else 0), -(da[(d, t)] / dn[d] if dn[d] else 0), -(gl[t] / tn if tn else 0))
    return key

B3 = {}
for _f in glob.glob(a.b3dir + "/b3_*.jsonl"):
    for _l in open(_f):
        _j = json.loads(_l); B3.setdefault(f"B3 LLM variant {_j['variant']} ({_j['model']})", {})[_j["change_id"]] = {t: i for i, t in enumerate(_j["ranking"])}

STOP_TOK = {"src", "test", "tests", "index", "ts", "d", "mts", "cts", "unit", "mod", "main"}
import re as _re
def toks(s):
    out = set()
    for piece in _re.split(r"[^A-Za-z0-9]+", s):
        for t in _re.findall(r"[A-Z]+(?![a-z])|[A-Z][a-z0-9]*|[a-z0-9]+", piece):
            t = t.lower()
            if t not in STOP_TOK: out.add(t)
    return out

def rankers(c, hist):
    m = meta[c]; g = graphs[m["parent"]]; tests = [r["test_file"] for r in changes[c]]; cov = {r["test_file"]: r["covers"] for r in changes[c]}
    start = g.locate(m["src_file"], m["line"])
    imp = g.bfs(g.rimp, f"file:{m['src_file']}"); call = g.bfs(g.rcall, start)
    tdist = {}
    for n, d in call.items():
        f = g.nodes.get(n, (0, ""))[1]
        if f: tdist[f] = min(tdist.get(f, INF), d)
    impd = lambda t: imp.get(f"file:{t}", INF)
    fid = g.locate(m["src_file"], m["line"])
    mt = toks(m["src_file"]) | (toks(fid.split("#", 1)[1]) if "#" in fid else set())
    fl = {r["test_file"]: r["fails"] for r in changes[c]}
    out = {"ORACLE (perfect order)": {t: -fl[t] for t in tests}, "B0 random": {t: 0 for t in tests},
           "B1 import-proximity": {t: impd(t) for t in tests},
           "B4 reverse-call reachability": {t: (tdist.get(t, INF), impd(t)) for t in tests},
           "B4c calls-only (no import tiebreak)": {t: tdist.get(t, INF) for t in tests},
           "B5a coverage, random order": {t: 1 - cov[t] for t in tests},
           "B5b coverage, most targeted first": {t: (1 - cov[t], covsize[m["parent"]].get(t, INF)) for t in tests},
           "B5d coverage, broadest first": {t: (1 - cov[t], -covsize[m["parent"]].get(t, 0)) for t in tests},
           "B6 call distance, ties broadest first": {t: (tdist.get(t, INF), -covsize[m["parent"]].get(t, 0)) for t in tests},
           "B7 lexical overlap": {t: -len(mt & toks(t)) for t in tests}}
    for nm, per in B3.items():
        if c in per: out[nm] = {t: per[c].get(t, INF) for t in tests}
    b3a = next((per for nm, per in B3.items() if "variant A" in nm), {})
    if c in b3a:
        b4pos = {t: i for i, t in enumerate(sorted(tests, key=lambda t: (tdist.get(t, INF), impd(t), t)))}
        out["B8 RRF(B3,B4)"] = {t: -(1 / (60 + b3a[c].get(t, INF)) + 1 / (60 + b4pos[t])) for t in tests}
    if hist:
        out["B2 history co-failure"] = {t: hist(m, t) for t in tests}
        out["B5c coverage, historical failure order"] = {t: (1 - cov[t], hist(m, t)) for t in tests}
    return out

def metrics(order, rows_by_t, restrict):
    cand = [t for t in order if (not restrict or rows_by_t[t]["covers"])]
    n = len(cand); pos = [i for i, t in enumerate(cand) if rows_by_t[t]["fails"]]; m = len(pos)
    if m == 0 or n == 0: return None
    res = {}
    for name, k in [("@1", 1), ("@3", 3), ("@5", 5), ("@5%", math.ceil(.05 * n)), ("@10%", math.ceil(.10 * n)), ("@20%", math.ceil(.20 * n))]:
        top = sum(1 for p in pos if p < k); res["recall" + name] = top / m; res["hit" + name] = float(top > 0)
    res["APFD"] = 1 - sum(p + 1 for p in pos) / (n * m) + 1 / (2 * n) if n > 1 else 1.0
    need = math.ceil(.95 * m); cum, tot = 0, sum(rows_by_t[t]["dur_ms"] for t in cand); seen = 0
    for i, t in enumerate(cand):
        cum += rows_by_t[t]["dur_ms"]; seen += rows_by_t[t]["fails"]
        if seen >= need: break
    res["time_frac_95"] = cum / tot if tot else 1.0
    ncov = sum(rows_by_t[t]["covers"] for t in rows_by_t)
    res["n95"] = i + 1; res["n95_vs_B5"] = (i + 1) / ncov
    return res

def evaluate(cs, hist, restrict):
    acc = collections.defaultdict(lambda: collections.defaultdict(list)); bucket = {}
    for c in cs:
        rb = {r["test_file"]: r for r in changes[c]}; ncov = sum(r["covers"] for r in changes[c]); b = "1" if ncov == 1 else "2-3" if ncov <= 3 else "4-10" if ncov <= 10 else ">10"
        if not any(r["fails"] for r in changes[c]): continue
        bucket[c] = b
        for name, key in rankers(c, hist).items():
            per_seed = []
            for s in range(a.seeds):
                rng = random.Random(f"{c}{s}"); order = sorted(rb, key=lambda t: (key[t], rng.random()))
                per_seed.append(metrics(order, rb, restrict))
            if per_seed[0] is None: continue
            avg = {k: statistics.mean(x[k] for x in per_seed) for k in per_seed[0]}; avg["_c"] = c; avg["_p"] = meta[c]["parent"]; avg["_f"] = meta[c]["src_file"]; avg["_fn"] = graphs[meta[c]["parent"]].locate(meta[c]["src_file"], meta[c]["line"]).split("@")[0].split("#", 1)[-1] + "|" + meta[c]["src_file"]; avg["ncov"] = ncov; avg["nfail"] = sum(r["fails"] for r in changes[c])
            acc[name]["_all"].append(avg); acc[name][b].append(avg)
            if b != "1": acc[name][">=2"].append(avg)
    return acc

KMIN = {"recall@1": 1, "recall@3": 3, "recall@5": 5, "hit@3": 3}
def cell(xs, c):
    if c in KMIN: xs = [x for x in xs if x["ncov"] > KMIN[c]]
    return f"{statistics.mean(x[c] for x in xs):.3f}" if xs else "-"

def table(acc, title):
    cols = ["recall@1", "recall@3", "recall@5", "recall@5%", "recall@10%", "recall@20%", "hit@3", "hit@10%", "APFD", "time_frac_95", "n95", "n95_vs_B5"]
    lines = [f"### {title}", "", "recall@1/3/5 and hit@3 average only over mutants with more covering tests than k (otherwise any ordering finds everything).", "", "| bucket | ranker | n | " + " | ".join(cols) + " |", "|" + "---|" * (len(cols) + 3)]
    for b in ["_all", ">=2", "1", "2-3", "4-10", ">10"]:
        for name in sorted(acc):
            xs = acc[name].get(b, [])
            if xs: lines.append(f"| {'all' if b == '_all' else 'cov' + b if b == '>=2' else 'cov=' + b} | {name} | {len(xs)} | " + " | ".join(cell(xs, c) for c in cols) + " |")
    return "\n".join(lines)

all_c = list(changes); train_c = [c for c in all_c if meta[c]["parent"] in train_parents]; test_c = [c for c in all_c if meta[c]["parent"] in test_parents]
train_files = {meta[c]["src_file"] for c in train_c}
strict_c = [c for c in test_c if meta[c]["src_file"] not in train_files]
hist = hist_model(train_c)
info = f"parents: {len(parents)} (train {len(train_parents)}, test {len(test_parents)}); mutants: all {len(all_c)}, train {len(train_c)}, test {len(test_c)}, test-with-unseen-file {len(strict_c)}; killed in test {sum(any(r['fails'] for r in changes[c]) for c in test_c)}, strict {sum(any(r['fails'] for r in changes[c]) for c in strict_c)}"
print(info); md = [f"# M3 baseline results\n\n{info}\n"]
for label, cs, h in [("TEST split (temporal), B2 trained on earlier parents", test_c, hist), ("TEST split restricted to files unseen in train (no same-file leakage)", strict_c, hist), ("ALL mutants (no training needed; B2 omitted)", all_c, None)]:
    for restrict, rl in [(False, "candidates = full suite"), (True, "candidates = covering tests only")]:
        md.append(table(evaluate(cs, h, restrict), f"{label} -- {rl}") + "\n")
open(a.out + ".md", "w").write("\n".join(md)); print("wrote", a.out + ".md")

# ---- failing fraction (oracle headroom) and clustered bootstrap CIs ----
def stratum(n): return "1" if n == 1 else "2-3" if n <= 3 else "4-10" if n <= 10 else ">10"
fr = collections.defaultdict(list)
for c in all_c:
    nf = sum(r["fails"] for r in changes[c]); nc = sum(r["covers"] for r in changes[c])
    if nf and nc: fr[stratum(nc)].append(nf / nc); fr[">=2"].extend([nf / nc] if nc > 1 else [])
q = lambda xs, p: sorted(xs)[min(len(xs) - 1, int(p * len(xs)))]
md2 = ["\n## Oracle headroom: failing fraction = failing tests / covering tests (killed mutants, all 337)\n", "Oracle n95/ncov is ceil(0.95*failing)/covering, so it is bounded below by this fraction. Median above 0.7 means little headroom inside the covering set.\n",
       "| stratum | n | median | p25 | p75 | mean | oracle n95/ncov (mean) | flag median>0.7 |", "|---|---|---|---|---|---|---|---|"]
orc = {}
for c in all_c:
    nf = sum(r["fails"] for r in changes[c]); nc = sum(r["covers"] for r in changes[c])
    if nf and nc: orc.setdefault(stratum(nc), []).append(math.ceil(.95 * nf) / nc); orc.setdefault(">=2", []).extend([math.ceil(.95 * nf) / nc] if nc > 1 else [])
for b in ["1", "2-3", "4-10", ">10", ">=2"]:
    x = fr[b]
    if x: md2.append(f"| {b} | {len(x)} | {statistics.median(x):.2f} | {q(x, .25):.2f} | {q(x, .75):.2f} | {statistics.mean(x):.2f} | {statistics.mean(orc[b]):.2f} | {'YES' if statistics.median(x) > .7 else 'no'} |")

def boot(accs, name, bucket, metric, base=None, B=2000, seed=0, key="_p"):
    """Cluster bootstrap over parent commits. Returns (mean, lo, hi). With `base`: paired difference name - base."""
    xs = [x for x in accs[name][bucket]]; byp = collections.defaultdict(list)
    if base: bm = {x["_c"]: x for x in accs[base][bucket]}
    for x in xs:
        if metric in KMIN and not x["ncov"] > KMIN[metric]: continue
        byp[x[key]].append(x[metric] - (bm[x["_c"]][metric] if base else 0))
    ps = list(byp); rng = random.Random(seed); ms = []
    for _ in range(B):
        v = [y for p in (rng.choice(ps) for _ in ps) for y in byp[p]]
        if v: ms.append(statistics.mean(v))
    allv = [y for p in ps for y in byp[p]]; ms.sort()
    return statistics.mean(allv), ms[int(.025 * len(ms))], ms[int(.975 * len(ms))]
accA = evaluate(all_c, None, False)
md2 += ["\n## Cluster-bootstrap 95% CIs (resample the 12 parent commits; ALL mutants, training-free rankers; full-suite candidates)\n", "Mutants from one commit are correlated, so the effective n is the number of commits (12). Differences are paired per mutant. Test-split-only CIs would have 4 clusters and are not reported.\n",
        "| stratum | metric | ranker | mean [95% CI] | paired diff vs B5a [95% CI] | paired diff vs B4 [95% CI] |", "|---|---|---|---|---|---|"]
for b in [">=2", ">10"]:
    for metric in ["n95_vs_B5", "recall@5", "APFD"]:
        for name in ["ORACLE (perfect order)", "B5a coverage, random order", "B5b coverage, most targeted first", "B4 reverse-call reachability", "B4c calls-only (no import tiebreak)", "B1 import-proximity"]:
            if not accA[name][b]: continue
            m, lo, hi = boot(accA, name, b, metric)
            d1 = boot(accA, name, b, metric, "B5a coverage, random order") if name != "B5a coverage, random order" else None
            d2 = boot(accA, name, b, metric, "B4 reverse-call reachability") if name != "B4 reverse-call reachability" else None
            f = lambda d: f"{d[0]:+.3f} [{d[1]:+.3f}, {d[2]:+.3f}]" if d else "-"
            md2.append(f"| {b} | {metric} | {name.split(' (')[0].split(',')[0]} | {m:.3f} [{lo:.3f}, {hi:.3f}] | {f(d1)} | {f(d2)} |")
open(a.out + ".md", "a").write("\n".join(md2) + "\n"); print("\n".join(md2[:12]))

# ---- M4 go/no-go (pre-registered): >10 stratum, ALL mutants. GO iff oracle n95/ncov CI upper < 0.5 is not required: point estimates must satisfy oracle < 0.5 AND B5a > 0.7 ----
go = ["\n## M4 go/no-go (stratum >10 covering tests)\n", "Rule: GO iff oracle n95/ncov < 0.5 AND B5a n95/ncov > 0.7 (B5a wastes most of the covering set). Commit-clustered 95% CIs shown; verdict uses point estimates and also says whether the CI agrees.\n"]
if accA["ORACLE (perfect order)"][">10"]:
    o = boot(accA, "ORACLE (perfect order)", ">10", "n95_vs_B5"); b5 = boot(accA, "B5a coverage, random order", ">10", "n95_vs_B5")
    nk = len(accA["ORACLE (perfect order)"][">10"]); ncm = len({x["_p"] for x in accA["ORACLE (perfect order)"][">10"]})
    ci_ok = o[2] < 0.5 and b5[1] > 0.7
    go.append(f"- killed mutants in stratum: {nk} from {ncm} commits\n- oracle n95/ncov: {o[0]:.3f} [{o[1]:.3f}, {o[2]:.3f}]\n- B5a n95/ncov: {b5[0]:.3f} [{b5[1]:.3f}, {b5[2]:.3f}]\n- VERDICT (point estimates): {'GO' if o[0] < .5 and b5[0] > .7 else 'NO-GO'}; CIs {'agree' if ci_ok == (o[0] < .5 and b5[0] > .7) else 'do not clearly agree'}")
open(a.out + ".md", "a").write("\n".join(go) + "\n"); print("\n".join(go))

# ---- ranking INSIDE the covering set (the M4 question): clustered CIs, ALL mutants, candidates = covering tests only ----
accR = evaluate(all_c, None, True); rr = ["\n## Inside the covering set: commit-clustered bootstrap CIs (ALL mutants, candidates = covering tests only)\n", "| stratum | metric | ranker | mean [95% CI] | paired diff vs B5a [95% CI] | paired diff vs B4 [95% CI] |", "|---|---|---|---|---|---|"]
for b in [">10", ">=2"]:
    for metric in ["n95", "recall@5", "APFD", "time_frac_95"]:
        for name in ["ORACLE (perfect order)", "B5a coverage, random order", "B5b coverage, most targeted first", "B5d coverage, broadest first", "B6 call distance, ties broadest first", "B4 reverse-call reachability", "B4c calls-only (no import tiebreak)", "B1 import-proximity", "B7 lexical overlap", "B8 RRF(B3,B4)"] + sorted(B3):
            if not accR[name][b]: continue
            m, lo, hi = boot(accR, name, b, metric); d = boot(accR, name, b, metric, "B5a coverage, random order") if not name.startswith("B5a") else None
            d4 = boot(accR, name, b, metric, "B4 reverse-call reachability") if name not in ("B4 reverse-call reachability", "B5a coverage, random order") else None
            rr.append(f"| {b} | {metric} | {name.split(' (')[0].split(',')[0]} | {m:.3f} [{lo:.3f}, {hi:.3f}] | {f'{d[0]:+.3f} [{d[1]:+.3f}, {d[2]:+.3f}]' if d else '-'} | {f'{d4[0]:+.3f} [{d4[1]:+.3f}, {d4[2]:+.3f}]' if d4 else '-'} |")
open(a.out + ".md", "a").write("\n".join(rr) + "\n"); print("\n".join(rr))

# ---- robustness: same inside-covering-set comparison clustered by commit, by source file, and by (file, function) ----
cn = collections.Counter(); st = accR["ORACLE (perfect order)"][">10"]
rob = ["\n## Robustness of the >10 stratum result to clustering (ALL mutants, candidates = covering tests only)\n",
       f"Stratum >10: {len(st)} killed mutants; distinct commits {len({x['_p'] for x in st})}, distinct source files {len({x['_f'] for x in st})}, distinct mutated functions {len({x['_fn'] for x in st})}.\n",
       "| ranker | metric | cluster by | paired diff vs B5a [95% CI] | paired diff vs B4 [95% CI] |", "|---|---|---|---|---|"]
for name in ["B4 reverse-call reachability", "B4c calls-only (no import tiebreak)", "B1 import-proximity", "B5d coverage, broadest first", "B6 call distance, ties broadest first", "B5b coverage, most targeted first", "B7 lexical overlap", "B8 RRF(B3,B4)", "ORACLE (perfect order)"] + sorted(B3):
    if not accR[name][">10"]: continue
    for metric in ["n95", "recall@5", "APFD"]:
        for lab, key in [("commit", "_p"), ("source file", "_f"), ("function", "_fn")]:
            d = boot(accR, name, ">10", metric, "B5a coverage, random order", key=key)
            d4 = boot(accR, name, ">10", metric, "B4 reverse-call reachability", key=key) if name != "B4 reverse-call reachability" else None
            rob.append(f"| {name.split(' (')[0]} | {metric} | {lab} | {d[0]:+.3f} [{d[1]:+.3f}, {d[2]:+.3f}] | {f'{d4[0]:+.3f} [{d4[1]:+.3f}, {d4[2]:+.3f}]' if d4 else '-'} |")
open(a.out + ".md", "a").write("\n".join(rob) + "\n"); print("\n".join(rob))
