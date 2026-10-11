#!/usr/bin/env python3
"""P0 pairs table: for each (repo snapshot, test file, function) -> covered(T,f) labels.
Labels from cov_P line coverage intersected with function node ranges in graphs.db.
Excludes: baseline-covered functions (empty-test run), non-green test files, functions
in test files themselves, .d.ts, and files with no executable lines (never covered anywhere).
Also emits per-snapshot sidecars: type-only import targets per file, vi/jest mock targets and
dynamic import() targets per test file (resolved from `git show` source, repo-relative paths).
Usage: pairs.py REPO_NAME M2DIRS DB REPO OUT.jsonl --baseline BL.json [--report OUT.md]"""
import argparse, bisect, collections, glob, json, re, sqlite3, subprocess
ap = argparse.ArgumentParser(); ap.add_argument("name"); ap.add_argument("m2dirs"); ap.add_argument("db"); ap.add_argument("repo"); ap.add_argument("out")
ap.add_argument("--baseline", default=""); ap.add_argument("--report", default="")
a = ap.parse_args()

isTest = re.compile(r"\.(test|spec)\.[cm]?[tj]sx?$")
con = sqlite3.connect(a.db)
recs = [json.load(open(f)) for d in a.m2dirs.split(",") for f in glob.glob(d + "/[0-9a-f]*.json")]
recs = [r for r in recs if "cov_P" in r and "parent" in r]

# ---------- sidecar source scans ----------
MOCK = re.compile(r"(?:vi|jest)\.mock\(\s*['\"]([^'\"]+)['\"]")
DYNI = re.compile(r"\bimport\(\s*['\"]([^'\"]+)['\"]")
TYPONLY = re.compile(r"^\s*import\s+type\s*(?:\{[^}]*\}|\*\s*as\s*\w+|\w+)?\s*from\s*['\"]([^'\"]+)['\"]", re.M)
def git_show(P, f):
    return subprocess.run(["git", "-C", a.repo, "show", f"{P}:{f}"], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
def resolve(spec, frm, files):
    if spec.startswith("."):
        base = frm.rsplit("/", 1)[0]
        parts = (base + "/" + spec).split("/"); out = []
        for p in parts:
            if p == "..": out = out[:-1]
            elif p != ".": out.append(p)
        stem = "/".join(out)
        for cand in (stem + ".ts", stem + ".tsx", stem + "/index.ts", stem + "/index.tsx"):
            if cand in files: return cand
        return stem
    m = spec if spec.startswith("node:") else "/".join(spec.split("/")[:2]) if spec.startswith("@") else spec.split("/")[0]
    return "module:" + m

# ---------- baseline mask (file-level, stable across commits) ----------
base_files = set()
if a.baseline:
    bl = json.load(open(a.baseline))
    for t, v in bl["tests"].items():
        base_files |= set(v["covered"])
base_files = {f for f in base_files if not isTest.search(f)}

# ---------- per-snapshot loop ----------
pairs_out = open(a.out, "w"); sig_out = open(a.out.replace(".jsonl", "_signals.jsonl"), "w")
stats = []
for r in sorted(recs, key=lambda r: r["parent"]):
    P = r["parent"]; tests = r["cov_P"]["tests"]
    spf = (r.get("suite_P") or {}).get("files", {})
    green = {t for t, v in spf.items() if v.get("status") == "pass"} if spf else set(tests)
    nodes = {i: (k, f, s, e) for i, k, f, s, e in con.execute(
        "SELECT id,kind,file,start_line,end_line FROM nodes WHERE commit_hash=? AND kind IN ('function','file')", (P,))}
    fn_by_file = collections.defaultdict(list)   # file -> [(start,end,funcid)]
    file_nodes = set()
    for i, (k, f, s, e) in nodes.items():
        if isTest.search(f): continue
        if k == "function": fn_by_file[f].append((s, e, i))
        else: file_nodes.add(f)
    for f in fn_by_file: fn_by_file[f].sort()
    # import edges (all kinds incl. type-only in the graph) for import-closure diagnostics
    imp = collections.defaultdict(set)
    for src, dst in con.execute("SELECT src,dst FROM edges WHERE commit_hash=? AND type='imports'", (P,)):
        imp[src].add(dst)
    # type-only targets per file (source scan; needed by heuristics C1)
    all_files = {n[1] for n in nodes.values()} | set(tests)
    typeonly = {}
    for f in all_files:
        src = git_show(P, f)
        tg = {resolve(m, f, file_nodes | set(tests)) for m in TYPONLY.findall(src)}
        if tg: typeonly[f] = sorted(tg)
    covered_any = set()
    for t, v in tests.items():
        covered_any |= set(v.get("covered", {}))
    # import closure (runtime only: strip type-only targets)
    def closure(t):
        seen, q = {f"file:{t}"}, [f"file:{t}"]
        while q:
            u = q.pop()
            for v in imp.get(u, ()):
                tgt = v[5:]
                if tgt in typeonly.get(u[5:], ()): continue
                if v not in seen: seen.add(v); q.append(v)
        return {x[5:] for x in seen if x.startswith("file:")}
    n_pairs = n_pos = 0; f_cov = f_clo = f_both = 0
    for t, v in tests.items():
        if green and t not in green: continue
        cov = {f: set(ls) for f, ls in v.get("covered", {}).items()}
        src = git_show(P, t)
        mocks = {resolve(m, t, file_nodes) for m in MOCK.findall(src)}
        dyns = {resolve(m, t, file_nodes) for m in DYNI.findall(src)}
        sig_out.write(json.dumps({"repo": a.name, "parent": P, "test": t, "mocks": sorted(mocks), "dyn": sorted(dyns)}) + "\n")
        clo = closure(t)
        for f, lines in cov.items():
            if f in base_files or isTest.search(f): continue
            f_cov += 1; f_both += 1 if f in clo else 0
        for f, flist in fn_by_file.items():
            lines = cov.get(f)
            if f in base_files: continue          # baseline-covered file -> excluded
            if f not in covered_any: continue     # no executable lines in ANY test -> excluded
            for s, e, fid in flist:
                ex = [l for l in lines if s <= l <= e] if lines else []
                covd = 1 if ex else 0
                n_pairs += 1; n_pos += covd
                pairs_out.write(json.dumps({"repo": a.name, "snapshot": P, "test": t, "func": fid, "file": f,
                                            "fstart": s, "fend": e, "covered": covd,
                                            "line_frac": round(len(ex) / max(1, e - s + 1), 4)}) + "\n")
    stats.append({"repo": a.name, "snapshot": P[:10], "tests": len(tests), "functions": sum(len(x) for x in fn_by_file.values()),
                  "pairs": n_pairs, "pos_rate": round(n_pos / max(1, n_pairs), 5),
                  "file_covered_in_closure": round(f_both / max(1, f_cov), 4), "n_file_covered": f_cov})
    print(stats[-1])
pairs_out.close(); sig_out.close()
if a.report:
    open(a.report, "w").write(json.dumps(stats, indent=1))
print("wrote", a.out)
