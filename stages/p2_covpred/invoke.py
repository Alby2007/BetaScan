"""Canonical test-invocation derivation (CI workflows -> package.json -> fallback)
plus failure-signature normalization. Shared by screen_repo.py; importable."""
import json, re

def ensure_run(cmd):
    toks = cmd.split()
    for i, t in enumerate(toks):
        if t == "vitest" or t.endswith("/vitest"):
            nxt = toks[i + 1] if i + 1 < len(toks) else ""
            if nxt not in ("run", "related", "bench", "watch", "dev", "--help"):
                toks.insert(i + 1, "run")
            break
    return " ".join(toks)

EXCL_STEP = re.compile(r"e2e|playwright|cypress|browser|chromium|selenium|storybook|docker|service|integration", re.I)
TYPE_STEP = re.compile(r"test:types?|--typecheck|\btsd\b|dtslint|type-tests?", re.I)
STRIP = re.compile(r"^--(coverage|reporter|shard|watch|ui|browser|bail)(=\S*)?$")

def strip_flags(cmd):
    """Remove coverage/reporter/shard/watch flags for pass+timing runs
    (coverage stays a separate step; shard/watch are CI artifacts)."""
    toks, out = cmd.split(), []
    i = 0
    while i < len(toks):
        t = toks[i]
        if STRIP.match(t):
            if "=" not in t and i + 1 < len(toks) and not toks[i + 1].startswith("-") and t == "--reporter":
                i += 1  # reporter takes a separate value token
            i += 1; continue
        out.append(t); i += 1
    return " ".join(out)

def derive_invocation(dest, pm):
    """Canonical test invocation: CI workflows first, package.json scripts second.
    Returns (vitest_prefix, alt_prefix, prebuild, source, candidates). *_prefix ends with '--outputFile'."""
    wds, wd = [], ""
    wfdir = dest / ".github" / "workflows"
    for y in sorted(wfdir.glob("*.y*ml")) if wfdir.exists() else []:
        lines = y.read_text(encoding="utf-8", errors="replace").splitlines()
        i = 0
        while i < len(lines):
            l = lines[i]
            m = re.match(r"\s*(?:-\s*)?working-directory\s*:\s*(\S+)", l)
            if m: wd = m.group(1).strip("\"'")
            m = re.match(r"\s*-?\s*run\s*:\s*(.*)", l)
            if m:
                body = m.group(1).strip()
                if body in ("|", ">", "|-", ">-", ""):
                    ind = len(l) - len(l.lstrip()); body = ""; i += 1
                    while i < len(lines) and lines[i].strip() and (len(lines[i]) - len(lines[i].lstrip())) > ind:
                        body += lines[i].strip() + " ; "; i += 1
                wds.append((wd, body.rstrip(" ;")))
            i += 1
    skip = re.compile(r"lint|format|typecheck|tsc|eslint|prettier|attw|publint", re.I)
    candidates = []
    testline, twd, buildline = "", "", ""
    for w, b in wds:
        segs = [s.strip() for s in re.split(r"&&|;", b) if s.strip()]
        tseg = next((s for s in segs if re.search(r"vitest|\btests?\b", s)), "")
        first = re.sub(r"^\s*(?:[A-Z_]+=\S+\s+)+", "", tseg).split()
        runner_start = bool(first) and (first[0] in ("pnpm", "npm", "yarn", "npx", "bunx", "node", "pnpx")
                                        or first[0].endswith("vitest") or first[0] == "vitest")
        if runner_start and tseg:
            b = tseg
            excl = bool(skip.search(b) or EXCL_STEP.search(b) or TYPE_STEP.search(b))
            candidates.append({"step": b, "wd": w, "excluded": excl,
                               "why": "lint/typecheck" if (skip.search(b) or TYPE_STEP.search(b))
                                     else "e2e/browser/service" if EXCL_STEP.search(b) else "candidate"})
            if not excl and not testline:
                testline, twd = b, w
        if re.search(r"\bbuild\b", b) and not skip.search(b) and not buildline:
            buildline = b
    src = "ci"
    if not testline:
        pj = dest / "package.json"
        script = json.loads(pj.read_text(encoding="utf-8")).get("scripts", {}).get("test", "") if pj.exists() else ""
        if re.fullmatch(r"(npx |pnpm exec |pnpm |bunx )?vitest\s*", script):
            testline = "npx vitest run"
        elif script:
            testline = f"{pm} test"
        src = "pkg" if testline else "fallback"
    cmd = ensure_run(strip_flags(testline)) if testline else "npx vitest run"
    if twd: cmd = f"cd {twd} && {cmd}"
    if re.match(r"npm (run |test)", cmd) or re.search(r"&&\s*npm (run |test)", cmd):
        cmd += " --"
    vprefix = cmd + " --reporter=json --outputFile"
    alt = (f"{pm} exec vitest run" if pm == "pnpm" else "yarn vitest run" if pm == "yarn"
           else "npx --no-install vitest run") + " --reporter=json --outputFile"
    alt = "" if vprefix == alt else alt
    # positional dir arg after 'run' (e.g. 'vitest run test/unit') scopes file selection
    toks = cmd.split(); scope = ""
    if "run" in toks:
        i = toks.index("run") + 1
        if i < len(toks) and not toks[i].startswith("-") and "/" in toks[i]:
            scope = toks[i]
    return vprefix, alt, buildline, src, candidates, scope

def normsig(tr_json):
    msgs = re.findall(r'"(?:failureMessages?|message)"\s*:\s*"([^"]{5,400})', tr_json)
    l = (msgs[0] if msgs else tr_json[:200]).split("\\n")[0]
    l = re.sub(r"[0-9a-f]{7,}", "#", l); l = re.sub(r"\d+", "#", l)
    l = re.sub(r"[^\w /.\-]", "", l); l = re.sub(r"\s+", " ", l).strip()
    return l[:80] or "?"
