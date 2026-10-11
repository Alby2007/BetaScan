#!/usr/bin/env python3
"""B3: an LLM reads the change (mutation shown as a diff, with surrounding source) and ranks the covering test files.
Usage: b3_llm.py ROWS.jsonl GRAPHS.db REPO OUTDIR --variant A|B [--model MODEL --provider anthropic|openai] [--dry-run] [--limit N]
Variant A: diff + source context + covering test paths (the same covering set and budget B4/B5 get; no labels, parent commit only).
Variant B: A + for each test, the src files it imports directly (a compact repo map, to check whether any gain is just "more context").
Fixed prompt, temperature 0, raw responses logged. Resumable. --dry-run writes prompts only (no API call). Key from ANTHROPIC_API_KEY / OPENAI_API_KEY."""
import argparse, collections, difflib, glob, json, os, pathlib, sqlite3, subprocess, sys, tarfile, tempfile, urllib.request
GEN = pathlib.Path(__file__).resolve().parents[1] / "m2_labeller" / "gen_mutants.mjs"
ap = argparse.ArgumentParser(); ap.add_argument("rows"); ap.add_argument("db"); ap.add_argument("repo"); ap.add_argument("outdir")
ap.add_argument("--variant", default="A"); ap.add_argument("--model", default=""); ap.add_argument("--provider", default="anthropic")
ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--limit", type=int, default=0); ap.add_argument("--min-cov", type=int, default=11)
ap.add_argument("--sample", type=int, default=0, help="random subset of this many changes (fixed seed)"); ap.add_argument("--seed", type=int, default=0); ap.add_argument("--sleep", type=float, default=7.0)
ap.add_argument("--mutdirs", default="data/m2_mut,data/m2b_mut")
a = ap.parse_args(); out = pathlib.Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
SYSTEM = ("You are helping prioritise tests in a TypeScript repository. A small code change was made. You are given the change and the list of test files "
          "that execute the changed line. Rank ALL listed test files from most likely to fail because of this change to least likely. "
          "Answer with JSON only: {\"ranking\": [\"path1\", \"path2\", ...]} containing every listed path exactly once.")
rows = collections.defaultdict(list)
for l in open(a.rows):
    r = json.loads(l); rows[r["change_id"]].append(r)
muts = {}
for d in a.mutdirs.split(","):
    for f in glob.glob(d + "/*.json"):
        j = json.load(open(f))
        if "parent" not in j or "mutants" not in j: continue
        for m in j["mutants"]: muts[f"{j['parent'][:10]}:{m['id']}"] = (j["parent"], m)
con = sqlite3.connect(a.db)
def src_at(P, f): return subprocess.run(["git", "-C", a.repo, "show", f"{P}:{f}"], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.splitlines()
def imports(P, t, top): return sorted(r[0][5:] for r in con.execute(f"SELECT dst FROM edges WHERE commit_hash=? AND type='imports' AND src=? AND dst LIKE 'file:{top}/%'", (P, f"file:{t}")))
_gen = {}
def mutated_diff(P, m):
    k = (P, m["file"])
    if k not in _gen:
        with tempfile.TemporaryDirectory() as wt:
            tar = pathlib.Path(wt) / "src.tar"
            subprocess.run(["git", "-C", a.repo, "archive", "-o", str(tar), P, m["file"].split("/")[0]], check=True)
            with tarfile.open(tar) as tf:
                tf.extractall(wt, filter="data", members=[m for m in tf.getmembers() if not (m.issym() or m.islnk())])
            _gen[k] = {f"{x['file']}:{x['start']}:{x['mutator']}": x for x in json.loads(subprocess.run(["node", str(GEN), wt, m["file"]], capture_output=True, text=True, encoding="utf-8", errors="replace", check=True).stdout)}
    g = _gen[k].get(m["id"])
    if g is None: return None
    text = "\n".join(src_at(P, m["file"])) + "\n"
    new = text[: g["start"]] + g["replacement"] + text[g["end"]:]
    return "\n".join(difflib.unified_diff(text.splitlines(), new.splitlines(), f"a/{m['file']}", f"b/{m['file']}", n=12, lineterm=""))
def prompt(c):
    P, m = muts[c]
    tests = sorted(r["test_file"] for r in rows[c] if r["covers"])
    d = mutated_diff(P, m)
    if d is None: return None, tests
    p = f"Change ({m['file']}, line {m['line']}):\n{d}\n\nCovering test files ({len(tests)}):\n"
    p += "\n".join((f"- {t}  (imports: {', '.join(imports(P, t, m['file'].split('/')[0])) or 'none'})" if a.variant == "B" else f"- {t}") for t in tests)
    return p, tests
todo = [c for c, rs in rows.items() if c in muts and any(r["fails"] for r in rs) and sum(r["covers"] for r in rs) >= a.min_cov]
if a.sample: import random; todo = random.Random(a.seed).sample(todo, min(a.sample, len(todo)))
todo = todo[: a.limit] if a.limit else todo
SERVED = {}
def call(p):
    import time
    if a.provider == "ollama":
        body = json.dumps({"model": a.model, "system": SYSTEM, "prompt": p, "stream": False, "format": "json", "options": {"temperature": 0}}).encode()
        for attempt in range(8):
            try:
                req = urllib.request.Request("http://localhost:11434/api/generate", body, {"content-type": "application/json"})
                return json.load(urllib.request.urlopen(req, timeout=300))["response"]
            except Exception:
                time.sleep(10 * (attempt + 1)); continue
        raise RuntimeError("ollama retries exhausted")
    if a.provider == "gemini":
        body = json.dumps({"systemInstruction": {"parts": [{"text": SYSTEM}]}, "contents": [{"role": "user", "parts": [{"text": p}]}], "generationConfig": {"temperature": 0, "responseMimeType": "application/json"}}).encode()
        for attempt in range(8):
            try:
                req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{a.model}:generateContent", body, {"x-goog-api-key": os.environ["GEMINI_API_KEY"], "content-type": "application/json"})
                time.sleep(a.sleep); r = json.load(urllib.request.urlopen(req, timeout=180)); SERVED["m"] = r.get("modelVersion"); return "".join(x.get("text", "") for x in r["candidates"][0]["content"]["parts"] if not x.get("thought"))
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 503): time.sleep(20 * (attempt + 1)); continue
                raise
            except Exception:
                time.sleep(20 * (attempt + 1)); continue
        raise RuntimeError("gemini retries exhausted")
    if a.provider == "anthropic":
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", json.dumps({"model": a.model, "max_tokens": 4000, "temperature": 0, "system": SYSTEM, "messages": [{"role": "user", "content": p}]}).encode(),
                                     {"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01", "content-type": "application/json"})
        return json.load(urllib.request.urlopen(req, timeout=180))["content"][0]["text"]
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions", json.dumps({"model": a.model, "temperature": 0, "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": p}]}).encode(),
                                 {"Authorization": "Bearer " + os.environ["OPENAI_API_KEY"], "content-type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=180))["choices"][0]["message"]["content"]
fo = out / f"b3_{a.variant}.jsonl"; done = {json.loads(l)["change_id"] for l in open(fo)} if fo.exists() else set()
(out / "SYSTEM_PROMPT.txt").write_text(SYSTEM)
print(len(todo), "changes in scope;", len(done), "done", file=sys.stderr)
for c in todo:
    if c in done: continue
    p, tests = prompt(c)
    if p is None: continue
    if a.dry_run:
        (out / f"prompt_{a.variant}_{c.replace('/', '_').replace(':', '_')[:80]}.txt").write_text(p); continue
    raw = call(p)
    try: rk = json.loads(raw[raw.index("{"): raw.rindex("}") + 1])["ranking"]
    except Exception: rk = []
    open(fo, "a").write(json.dumps({"change_id": c, "model": a.model, "variant": a.variant, "served": SERVED.get("m"), "ranking": rk, "n_tests": len(tests), "prompt": p, "raw": raw}) + "\n")
