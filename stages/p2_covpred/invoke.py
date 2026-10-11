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

def derive_invocation(dest, pm):
    """Canonical test invocation: CI workflows first, package.json scripts second.
    Returns (vitest_prefix, alt_prefix, prebuild, source). *_prefix ends with '--outputFile'."""
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
    testline, twd, buildline = "", "", ""
    for w, b in wds:
        if re.search(r"vitest|\btests?\b", b) and not skip.search(b):
            testline, twd = b, w; break
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
    cmd = ensure_run(testline) if testline else "npx vitest run"
    if twd: cmd = f"cd {twd} && {cmd}"
    if re.match(r"npm (run |test)", cmd) or re.search(r"&&\s*npm (run |test)", cmd):
        cmd += " --"
    vprefix = cmd + " --reporter=json --outputFile"
    plain = "npx vitest run --reporter=json --outputFile"
    alt = "" if vprefix == plain else plain
    return vprefix, alt, buildline, src

def normsig(tr_json):
    msgs = re.findall(r'"(?:failureMessages?|message)"\s*:\s*"([^"]{5,400})', tr_json)
    l = (msgs[0] if msgs else tr_json[:200]).split("\\n")[0]
    l = re.sub(r"[0-9a-f]{7,}", "#", l); l = re.sub(r"\d+", "#", l)
    l = re.sub(r"[^\w /.\-]", "", l); l = re.sub(r"\s+", " ", l).strip()
    return l[:80] or "?"
