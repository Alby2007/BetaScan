#!/usr/bin/env python3
"""Statement-level import classification: an (src->dst) import is runtime iff at least
one import/export statement in src references dst outside type position. Type-only iff
every referencing statement is `import type`/`export type`/`{type X}`-only.
imp_specs(src_text) -> (runtime_specs, typeonly_specs) as raw specifier strings."""
import re

FROM = re.compile(r"^\s*(import|export)\s+(.+?)\s+from\s*['\"]([^'\"]+)['\"]", re.M)
BARE = re.compile(r"^\s*import\s*['\"]([^'\"]+)['\"]", re.M)
TYPEKW = re.compile(r"type\b")

def _all_type(clause):
    """{ type A, type B } named-clause containing only type imports."""
    c = clause.strip()
    if c.startswith("{") and c.endswith("}"):
        parts = [p.strip() for p in c[1:-1].split(",") if p.strip()]
        return bool(parts) and all(p.startswith("type ") for p in parts)
    return False

def imp_specs(src):
    run, typ = set(), set()
    for kw, clause, spec in FROM.findall(src):
        if TYPEKW.match(clause.lstrip()) or _all_type(clause):  # `import type X` / `export type X` / `{type A}`-only
            typ.add(spec)
        else:
            run.add(spec)
    for spec in BARE.findall(src):
        run.add(spec)
    return run, typ - run   # a spec in BOTH is runtime


# ---------- shared graph helpers ----------
import collections, json, subprocess, bisect

def git_show(repo, P, f):
    return subprocess.run(["git", "-C", repo, "show", f"{P}:{f}"], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout

def resolve(spec, frm, files=()):
    if not spec.startswith("."):
        m = spec if spec.startswith("node:") else "/".join(spec.split("/")[:2]) if spec.startswith("@") else spec.split("/")[0]
        return "module:" + m
    base = frm.rsplit("/", 1)[0]; out = []
    for p in (base + "/" + spec).split("/"):
        if p == "..": out = out[:-1]
        elif p != ".": out.append(p)
    stem = "/".join(out)
    for cand in (stem + ".ts", stem + ".tsx", stem + "/index.ts", stem + "/index.tsx"):
        if cand in files: return cand
    return stem

def bfs(adj, start):
    d, q = {start: 0}, collections.deque([start])
    while q:
        u = q.popleft()
        for v in adj.get(u, ()):
            if v not in d: d[v] = d[u] + 1; q.append(v)
    return d

STOP = {"src", "test", "tests", "index", "ts", "d", "mts", "cts", "unit", "mod", "main"}
def toks(s):
    out = set()
    for piece in re.split(r"[^A-Za-z0-9]+", s):
        for t in re.findall(r"[A-Z]+(?![a-z])|[A-Z][a-z0-9]*|[a-z0-9]+", piece):
            t = t.lower()
            if t not in STOP: out.add(t)
    return out

def runtime_adj(con, repo, P, files):
    """imports adjacency minus type-only-only targets (statement-level)."""
    imp = collections.defaultdict(set)
    for s, d in con.execute("SELECT src,dst FROM edges WHERE commit_hash=? AND type='imports'", (P,)):
        imp[s].add(d)
    typeonly = {}
    for f in files:
        rs, ts = imp_specs(git_show(repo, P, f))
        tg = {resolve(m, f, files) for m in ts} - {resolve(m, f, files) for m in rs}
        if tg: typeonly[f] = tg
    rt = collections.defaultdict(set)
    for s, ds in imp.items():
        for d in ds:
            if d[5:] not in typeonly.get(s[5:], ()): rt[s].add(d)
    return rt, imp

def pkgdirs(repo, P):
    """in-repo package.json name -> dir (depth<=3, non-root)."""
    out = {}
    o = subprocess.run(["git", "-C", repo, "ls-tree", "-r", "--name-only", P], capture_output=True, text=True).stdout
    for pj in o.splitlines():
        if pj.endswith("package.json") and pj.count("/") <= 3 and "node_modules" not in pj and "/" in pj:
            try: nm = json.loads(git_show(repo, P, pj)).get("name")
            except Exception: nm = None
            if nm: out[nm] = pj.rsplit("/", 1)[0]
    return out

def imp_dist(rt_adj, t, pkg, files, INF=10**6):
    """file-level import distance from test t, with workspace module: expansion."""
    idist = bfs(rt_adj, f"file:{t}")
    for n, d in list(idist.items()):
        if n.startswith("module:") and n[7:] in pkg:
            dd = pkg[n[7:]] + "/"
            for f in files:
                if f.startswith(dd) and d + 1 < idist.get(f"file:{f}", INF): idist[f"file:{f}"] = d + 1
    return idist
