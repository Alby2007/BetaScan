#!/usr/bin/env python3
"""Scope the coverage-blind stratum: files that tests depend on but that line coverage of src/ cannot map to tests.
Usage: scope_blind_files.py REPO GRAPH.db COMMIT. Counts, per support file, test files that import it (transitively, via the M1 graph)
or reference it by a path string (assets/config). No mutation is run."""
import collections, re, sqlite3, subprocess, sys
repo, db, commit = sys.argv[1:4]
git = lambda *a: subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True, encoding="utf-8", errors="replace", check=True).stdout
files = git("ls-tree", "-r", "--name-only", commit).split()
is_test = lambda f: re.search(r"\.test(-d)?\.[cm]?tsx?$", f)
tests = [f for f in files if is_test(f) and not f.startswith("test/bench/")] ; tests_all = [f for f in files if is_test(f)]
con = sqlite3.connect(db)
rimp = collections.defaultdict(set)
for s, d in con.execute("SELECT src,dst FROM edges WHERE type='imports' AND commit_hash=?", (commit,)): rimp[d].add(s)
def reach(f):
    seen, q = {f"file:{f}"}, [f"file:{f}"]
    while q:
        u = q.pop()
        for v in rimp.get(u, ()):
            if v not in seen: seen.add(v); q.append(v)
    return {x[5:] for x in seen if x.startswith("file:") and is_test(x[5:])}
support = [f for f in files if f.startswith("test/") and not is_test(f) and f.endswith((".ts", ".mts", ".js", ".mjs"))]
assets = [f for f in files if f.startswith("test/") and not is_test(f) and f not in support]
config = [f for f in files if re.match(r"(vitest\.config\.\w+|tsconfig\.json|package\.json|pnpm-workspace\.yaml|build\.config\.ts|\.github/workflows/ci\.yml)$", f)]
src_text = {t: git("show", f"{commit}:{t}") for t in tests_all}
rows = []
for f in support:
    r = reach(f); rows.append(("support-code", f, len(r), "import graph"))
for f in assets:
    base = f.split("/")[-1]; r = [t for t, x in src_text.items() if base in x]; rows.append(("asset/fixture", f, len(r), "path string match"))
for f in config:
    rows.append(("config", f, len(tests_all), "global (all tests run under it)"))
dist = [t for t, x in src_text.items() if "dist/" in x or "/dist" in x]
rows.append(("build-output", "dist/ (build artefact)", len(dist), "path string match, " + ", ".join(dist[:3])))
print(f"commit {commit[:8]}: {len(tests_all)} test files total\n\n| kind | file | test files reached | how |\n|---|---|---|---|")
for k, f, n, h in sorted(rows, key=lambda r: (r[0], -r[2])): print(f"| {k} | {f} | {n} | {h} |")
agg = collections.defaultdict(lambda: [0, set()])
for k, f, n, h in rows: agg[k][0] += 1
print("\nsupport files with >=1 reaching test:", sum(1 for k, f, n, h in rows if k == "support-code" and n), "of", len(support))
print("distinct test files reached by support/asset files (excluding config):", len({t for k, f, n, h in rows if k in ('support-code',) for t in reach(f)}))
