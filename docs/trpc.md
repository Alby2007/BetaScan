# trpc held-out repo

Held-out evaluation repo: [`trpc/trpc`](https://github.com/trpc/trpc) clone at
`targets_scope/full__trpc__trpc` (~4.9k commits). Chosen over zod (deterministic but fragile
install across history) and other unjs repos (thin `>10` strata).

## Scope

- **Mutation targets:** `packages/{server,client}/src` only
- **Test scope:** test files under `packages/{server,client,tests}` — `packages/tests` is the
  integration suite exercising server+client. react-query/tanstack/next/openapi/upgrade excluded.
- **Green set:** files passing **both** clean suite runs (`excluded_files` on the record).
  `packages/tests/server/websockets.test.ts` is flaky at HEAD — excluded per-parent.

## Era routing

`engines.node` is `^22.18.0` before ~May 2026 (pnpm 9) and `^24` after (pnpm 10→12).
`pilot.py::image_for()` picks `impactnet-node22` vs `impactnet-node` per parent commit —
**required**: Node-22-era commits under Node 24 fail ~45/97 scoped test files on an undici
`AbortSignal` realm check.

## Differences from the h3 pipeline

| Aspect | h3 | trpc |
|---|---|---|
| Records | m2 (suite/cov) + m2b_mut (mutants) in separate dirs | single `<C>.json` per commit, mutants inline |
| Config | vitest config override (`vitest.mut.config.mjs`) | none — workspace aliases required |
| vitest retry | default | `--retry=0` (trpc's shared config sets retry:2 under CI — would mask kills) |
| timeouts | 120s batch / 45s split | 300s batch / 90s split (heavier test files) |
| install | `pnpm install --frozen-lockfile` | same + `COREPACK_ENABLE_STRICT=0` |
| mutants per commit | ≤8, ≤6 files | 25, round-robin across ALL eligible src files (≥11 covering green tests) — maximizes distinct files/functions; ~68 eligible files/parent |
| suite runs | suite_P + suite_C | suite×2 at P in one container (green = pass both) |
| flake log | separate `flake_log.py` runs | folded into the dual suite runs |

Mutation operators are **identical** (`gen_mutants.mjs` unchanged). `run_mutants.mjs` in
`stages/m2_labeller/trpc/` is the harness-adapted variant.

## Running

```bash
python stages/m2_labeller/trpc/pilot.py targets_scope/full__trpc__trpc data/trpc_pilot --n 7 --per-commit 25
```

Resumable: `<C>.json` exists → skipped; mid-run commits rerun from scratch; failures write
`<C>.skip` and the loop continues. Per commit: one combined container (install → suite1 →
per-file coverage → suite2, ~12–16 min warm) then a mutant container (~30–40 min for 25).

`summary.json` is written when the run finishes. Watch `n_src_files_eligible` — two old parents
had only 6 eligible files; the new config targets ≥30 distinct mutant files overall.

## Downstream

```bash
python stages/m3_baselines/extract_graphs.py targets_scope/full__trpc__trpc data/trpc_pilot data/trpc_graphs.db
python stages/m2_labeller/trpc/build_rows.py targets_scope/full__trpc__trpc data/trpc_pilot data/trpc_rows.jsonl
python stages/m3_baselines/evaluate.py data/trpc_rows.jsonl data/trpc_graphs.db data/trpc_eval \
    --m2dir data/trpc_pilot --b3dir data/trpc_b3 --test-parents 1
python stages/m3_baselines/b3_llm.py data/trpc_rows.jsonl data/trpc_graphs.db targets_scope/full__trpc__trpc \
    data/trpc_b3 --variant A --provider gemini --model gemini-flash-lite-latest
```

(`b3_llm.py` expects h3-style `src/` mutation paths for its diff builder — verify before running
B3 on trpc, whose src files live under `packages/*/src/`.)

## Sampling caveat (pre-registered for the write-up)

Round-robin mutant selection weights source files **equally**, not by real change frequency —
metrics are ranking-quality measures, not population rates. The records log
`n_src_files_eligible`, `src_files_below_min_cov`, `mutants_below_min_cov` for the
selection-effect audit.
