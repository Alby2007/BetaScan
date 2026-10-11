#!/usr/bin/env python3
"""Residual breakdown: classify each (test, covered-file) pair NOT in runtime import
closure by cause: DYN (dynamic import in test), MOCK (vi/jest.mock'd), MISSING_EDGE
(a source import spec resolves to the file but the graph has no edge), WS_PKG (file
under a workspace package whose name is a module: node in closure), OTHER.
Also reports C1 (runtime closure) function-level precision/recall from the pairs table.
Usage: residual.py NAME M2DIRS DB REPO PAIRS.jsonl[.gz] SIGNALS.jsonl --out rep.md"""
import argparse, collections, gzip, glob, json, os, re, sqlite3, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from impclass import imp_specs
ap = argparse.ArgumentParser()
for x in ["name","m2dirs","db","repo","pairs","signals"]: ap.add_argument(x)
ap.add_argument("--out", default="")
a = ap.parse_args()
isTest = re.compile(r"\.(test|spec)\.[cm]?[tj]sx?$")
con = sqlite3.connect(a.db)
recs = [json.load(open(f)) for d in a.m2dirs.split(",") for f in glob.glob(d + "/[0-9a-f]*.json")]
recs = [r for r in recs if "cov_P" in r and "parent" in r]

def git_show(P, f):
    return subprocess.run(["git", "-C", a.repo, "show", f"{P}:{f}"], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
def git_ls(P):
    o = subprocess.run(["git", "-C", a.repo, "ls-tree", "-r", "--name-only", P], capture_output=True, text=True).stdout
    return o.splitlines()
def resolve(spec, frm, files):
    if spec.startswith("."):
        base = frm.rsplit("/", 1)[0]; out = []
        for p in (base + "/" + spec).split("/"):
            if p == "..": out = out[:-1]
            elif p != ".": out.append(p)
        stem = "/".join(out)
        for cand in (stem + ".ts", stem + ".tsx", stem + "/index.ts", stem + "/index.tsx"):
            if cand in files: return cand
        return stem
    m = spec if spec.startswith("node:") else "/".join(spec.split("/")[:2]) if spec.startswith("@") else spec.split("/")[0]
    return "module:" + m

sigs = {}
for l in open(a.signals):
    d = json.loads(l); sigs[(d["parent"], d["test"])] = d

op = gzip.open if a.pairs.endswith(".gz") else open
pair_rows = collections.defaultdict(list)
for l in op(a.pairs, "rt"):
    d = json.loads(l); pair_rows[(d["snapshot"], d["test"])].append(d)

causes = collections.Counter(); examples = collections.defaultdict(list)
c1tp = c1fp = c1fn = 0
for r in sorted(recs, key=lambda r: r["parent"]):
    P = r["parent"]; tests = r["cov_P"]["tests"]
    spf = (r.get("suite_P") or {}).get("files", {})
    green = {t for t, v in spf.items() if v.get("status") == "pass"} if spf else set(tests)
    nodes = {i: (k, f) for i, k, f in con.execute("SELECT id,kind,file FROM nodes WHERE commit_hash=? AND kind IN ('function','file')", (P,))}
    file_nodes = {f for k, f in nodes.values() if k == "file" and not isTest.search(f)}
    imp = collections.defaultdict(set)
    for s, d in con.execute("SELECT src,dst FROM edges WHERE commit_hash=? AND type='imports'", (P,)):
        imp[s].add(d)
    all_files = {n[1] for n in nodes.values()} | set(tests)
    typeonly = {}
    for f in all_files:
        rs, ts = imp_specs(git_show(P, f))
        fs = file_nodes | set(tests)
        tg = {resolve(m, f, fs) for m in ts} - {resolve(m, f, fs) for m in rs}
        if tg: typeonly[f] = tg
    # workspace package name -> dir (package.json files at depth<=3 with a "name")
    pkgdir = {}
    for pj in git_ls(P):
        if pj.endswith("package.json") and pj.count("/") <= 3 and "node_modules" not in pj:
            try: nm = json.loads(git_show(P, pj)).get("name")
            except Exception: nm = None
            if nm: pkgdir[pj.rsplit("/", 1)[0] if "/" in pj else ""] = nm
    def closure(t):
        seen, q = {"file:" + t}, ["file:" + t]
        while q:
            u = q.pop()
            for v in imp.get(u, ()):
                if v[5:] in typeonly.get(u[5:], ()): continue
                if v not in seen: seen.add(v); q.append(v)
        return seen
    # all import specs per file (for MISSING_EDGE check) — lazily built
    specscan = {}
    def specs_of(f):
        if f not in specscan:
            rs, ts = imp_specs(git_show(P, f))
            specscan[f] = {resolve(m, f, file_nodes | set(tests)) for m in rs | ts}
        return specscan[f]
    for t, v in tests.items():
        if green and t not in green: continue
        seen = closure(t); clo = {x[5:] for x in seen if x.startswith("file:")}
        clo_files = clo | {t}
        mods = {x for x in seen if x.startswith("module:")}
        dyn = {resolve(m, t, file_nodes) for m in sigs.get((P, t), {}).get("dyn", [])}
        mocks = set()
        for m in sigs.get((P, t), {}).get("mocks", []):
            if not m.startswith("module:"):
                stem = m
                for cand in (stem + ".ts", stem + ".tsx", stem + "/index.ts", stem + "/index.tsx"):
                    if cand in file_nodes: stem = cand; break
                mocks.add(stem)
        for f in v.get("covered", {}):
            if isTest.search(f) or f in clo: continue
            if f in dyn: c = "DYN"
            elif f in mocks: c = "MOCK"
            elif any(f.startswith(d + "/") and ("module:" + nm) in mods for d, nm in pkgdir.items() if d): c = "WS_PKG"
            elif any(f in specs_of(cf) for cf in clo_files): c = "MISSING_EDGE"
            else: c = "OTHER"
            causes[c] += 1
            if len(examples[c]) < 8: examples[c].append(f"{P[:10]} {t} -> {f}")
        # C1 function-level P/R: predicted positive = func's file in runtime closure
        for row in pair_rows.get((P, t), ()):
            pred = row["file"] in clo
            if row["covered"] and pred: c1tp += 1
            elif row["covered"]: c1fn += 1
            elif pred: c1fp += 1
rep = ["# Residual breakdown + C1 precision/recall\n", "## causes (test, covered-file) pairs outside runtime closure\n",
       "| cause | n |", "|---|---|"]
for c, n in causes.most_common(): rep.append(f"| {c} | {n} |")
rep.append("\n## examples\n")
for c, xs in examples.items():
    rep.append(f"**{c}**")
    rep += [f"- `{x}`" for x in xs[:8]]
p = c1tp / max(1, c1tp + c1fp); rc = c1tp / max(1, c1tp + c1fn)
rep.append(f"\n## C1 runtime-closure classifier, function level\n\n- precision {p:.3f} · recall {rc:.3f} (tp={c1tp} fp={c1fp} fn={c1fn})\n")
out = "\n".join(rep)
print(out)
if a.out: open(a.out, "w").write(out)
