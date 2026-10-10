#!/usr/bin/env python3
"""Cheap, no-execution screen of candidate TS repos (import-graph proxy for the two strata we care about).
Usage: scope_repos.py OUT.md owner/repo [owner/repo ...]   (shallow-clones into targets_scope/, runs the M1 extractor, 5 min cap per repo)
Per repo: test files; share of src code (file line spans) in files transitively imported by >10 test files (proxy for the >10-covering-tests stratum);
support/fixture files and how many test files they reach (proxy for the coverage-blind stratum). Real coverage is NOT measured here."""
import collections, json, os, pathlib, re, subprocess, sys, tempfile
root = pathlib.Path(__file__).resolve().parents[2]; M1 = root / "stages/m1_extractor"
out, repos = sys.argv[1], sys.argv[2:]
isTest = lambda f: re.search(r"\.(test|spec)(-d)?\.[cm]?[tj]sx?$", f)
isSupport = lambda f: re.search(r"(^|/)(tests?|__tests__|fixtures?|__mocks__|test-utils?|testing)(/|$)", f) and not isTest(f)
rows = []
for r in repos:
    d = root / "targets_scope" / r.replace("/", "__")
    try:
        if not d.exists(): subprocess.run(["git", "clone", "--depth", "1", "-q", f"https://github.com/{r}", str(d)], check=True, timeout=300)
        commits = subprocess.run(["git", "-C", str(d), "rev-list", "--count", "HEAD"], capture_output=True, text=True).stdout.strip()
        p = subprocess.run(["node", str(M1 / "extract.mjs"), str(d)], capture_output=True, text=True, timeout=300)
        g = json.loads(p.stdout)
    except Exception as e:
        rows.append(f"| {r} | - | - | - | - | - | failed: {str(e)[:60]} |"); continue
    nodes = {n["id"]: n for n in g["nodes"] if n["kind"] in ("file", "test_file")}
    rimp = collections.defaultdict(set)
    for e in g["edges"]:
        if e["type"] == "imports": rimp[e["dst"]].add(e["src"])
    def reach(f):
        seen, q = {f}, [f]
        while q:
            for v in rimp.get(q.pop(), ()):
                if v not in seen: seen.add(v); q.append(v)
        return {x for x in seen if x in nodes and nodes[x]["kind"] == "test_file"}
    tests = [n for n in nodes.values() if n["kind"] == "test_file"]
    src = [n for n in nodes.values() if n["kind"] == "file" and not isSupport(n["file"]) and not re.search(r"(^|/)(docs?|examples?|playground|scripts?|bench\w*)/", n["file"])]
    tot = sum(n["end"] for n in src) or 1; big = sum(n["end"] for n in src if len(reach(n["id"])) > 10)
    sup = [n for n in nodes.values() if n["kind"] == "file" and isSupport(n["file"])]
    sr = {n["file"]: len(reach(n["id"])) for n in sup}; useful = [f for f, c in sr.items() if c >= 5]
    union = len({t for n in sup if len(reach(n["id"])) >= 5 for t in reach(n["id"])})
    rows.append(f"| {r} | {commits} (shallow) | {len(tests)} | {len(src)} | {100 * big / tot:.0f}% | {len(useful)} files reach {union} tests | ok |")
open(out, "w").write("| repo | commits | test files | src files | % src lines in files reached by >10 tests | support files reaching >=5 tests | status |\n|---|---|---|---|---|---|---|\n" + "\n".join(rows) + "\n")
print(open(out).read())
