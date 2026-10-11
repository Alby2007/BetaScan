# Setup

Everything that is NOT in the repo and must be restored on a new machine.

## Toolchain

| Tool | Version | Notes |
|---|---|---|
| Python | 3.13+ (3.14 used) | stdlib only for all stages — no pip deps |
| Node | 24 (host) | only for `extract.mjs` / `gen_mutants.mjs` (ts-morph) |
| Docker | Desktop w/ Linux containers | test suites + mutation runs happen inside containers |
| pnpm | inside containers only | via corepack |

## Target clones (gitignored)

```bash
git clone https://github.com/unjs/h3 targets/h3
git clone https://github.com/trpc/trpc targets_scope/full__trpc__trpc
```

The pipeline uses their git history (`git archive`, `git show`, `rev-list`); the checked-out
working tree state does not matter.

## ts-morph

`stages/m2_labeller/node_modules` should point at `stages/m1_extractor/node_modules`
(**gitignored, not committed** — a committed symlink kept being deleted on Windows
where `core.symlinks=false` materialises it as a plain file). The mutator scripts
(`gen_mutants.mjs`, `run_mutants.mjs`) resolve `ts-morph` through it.

```bash
cd stages/m1_extractor && npm install     # package-lock.json committed
```

Then create the link:

```bash
# POSIX
ln -s ../m1_extractor/node_modules stages/m2_labeller/node_modules
```

```cmd
:: Windows — junction, no admin needed
cd stages\m2_labeller
rmdir node_modules 2>nul & del node_modules
mklink /J node_modules ..\m1_extractor\node_modules
```

## Docker

```bash
docker build -f docker/Dockerfile        -t impactnet-node    docker/   # node:24-slim era
docker build -f docker/Dockerfile.node22 -t impactnet-node22  docker/   # node:22-slim era
```

Both images: `node:{ver}-slim` + git, ca-certificates, python3, procps, `corepack enable`.

**Volumes** (auto-created, persist across runs — the pnpm store is the difference between a
~16 min and ~5 min install for trpc Node-22-era commits):

- `impactnet-pnpm-store` → `/root/.local/share/pnpm`
- `impactnet-root-cache` → `/root/.cache` (playwright/prisma postinstall downloads, trpc)

**Era routing** (trpc only): `pilot.py::image_for()` reads `package.json` `engines.node` at the
parent commit — `^22` → `impactnet-node22`, else `impactnet-node`. Running a Node-22-era trpc
commit under Node 24 breaks ~45 test files (undici `AbortSignal` realm check changed).

## Secrets

`.secrets/gemini_key` — Gemini API key for B3, gitignored. `b3_llm.py` reads `GEMINI_API_KEY`
from the environment:

```bash
export GEMINI_API_KEY=$(cat .secrets/gemini_key)   # bash
$env:GEMINI_API_KEY = Get-Content .secrets/gemini_key   # powershell
```

Model used: `gemini-flash-lite-latest` (served `gemini-3.5-flash-lite`), temp 0, free tier.
Only public-repo code is sent. Never commit the key.

## Windows portability notes

The stages were written on Linux; three classes of fixes were needed on Windows (already applied):

1. **`extract.mjs` path separators** — `inRepo()` compared forward-slash `getFilePath()` against a
   backslash root → 0 nodes. Both normalized to `/` (no-op on Linux).
2. **`git archive | tar` host-side pipes** — under `shell=True` they hit System32 bsdtar which
   can't parse `-C C:\path`. Replaced with `git archive -o` + Python `tarfile` (regular files
   only; h3's one docs symlink is skipped).
3. **`subprocess.run(text=True)`** — decodes with cp1252 → `UnicodeDecodeError` on UTF-8/box-draw
   bytes in pnpm/vitest output, killing the reader thread. All sites now use
   `encoding="utf-8", errors="replace"`.

All tar/pnpm/vitest commands inside `bash -c "..."` scripts run in Linux containers and are
unaffected.

## Disk layout (P2+)

Docker's data disk lives on A: (external USB HDD) via an NTFS junction at
`%LOCALAPPDATA%\Docker\wsl\disk -> A:\DockerWSL\disk`. Screen clones go to
`A:\BetaScan_screen` and the pnpm store to `A:\pnpm-store` (host mount).
To keep A: awake during unattended runs, USB selective suspend and disk sleep
are disabled on AC power:

    powercfg -SETACVALUEINDEX SCHEME_CURRENT 2a737441-1930-4402-8d77-b2bebba308a3 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 0
    powercfg -SETACVALUEINDEX SCHEME_CURRENT 0012ee47-9041-4b5d-9b77-535fba8b1442 6738e2c4-e8a5-4a42-b16a-e040e769756e 0
    powercfg -SETACTIVE SCHEME_CURRENT

If A: is absent at start, the screen pauses up to 2h rather than failing repos.
Revert: stop Docker, delete the junction, recreate the `disk` folder.
