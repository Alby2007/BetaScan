# P2 repo selection proposal (for review — no collection started)

## Selection criteria (objective, logged)

In: TypeScript source, Vitest suite, public GitHub repo, `pnpm`/`npm`/`yarn` installable,
suite ≤ ~10 min wall, deterministic (no external services/keys/models), not a fork.
Out (logged with reason): non-Vitest runners (jest/mocha/ava/tap/bun:test/deno/node:test),
heavy external deps (playwright downloads, model weights, API keys), rust/go build steps,
>10 min suites, near-duplicates/forks. Per-file flakiness/failures are handled at
file level: a repo passes if ≥90% of test files are green identically in both runs
(flaky + consistently-failing files excluded at harvest, as on trpc).

## Validation grouping: maintainer ecosystem, cap 2

Validation folds group by **maintainer ecosystem** (shared conventions/utilities), not
just GitHub org. Leave-one-ecosystem-out; cap **2 repos per ecosystem**.

| ecosystem | cap used | notes |
|---|---|---|
| unjs | h3 (dev) + nitro | unstorage/ofetch/consola/c12 excluded — cap full |
| antfu | unocss + unplugin | antfu spans unocss/unplugin/shiki/vueuse → shiki, vueuse excluded |
| dai-shi (pmndrs) | jotai + valtio | |
| vuejs | pinia + vitepress | |
| hey-api | openapi-ts + openapi-fetch | |
| others | 1–2 each | TanStack, drizzle, valibot, arktype, astro, svelte, hono, etc. |

**orpc** stays in the training pool but is `exclude-from-trpc-folds`: it shares trpc's
domain (links, procedures, registration — the exact indirection behind B4's misses), so
it is never in a training fold when trpc is the held-out target.

## Automated screen → final list

`stages/p2_covpred/screen_repo.py` (Docker, same images as the coverage harness) does,
per candidate: shallow clone (HEAD sha recorded — harvest checks out that sha) →
detect runner → install → repo's own `test` script once (chains logged) →
**canonical vitest invocation derived from `.github/workflows`** (cwd, flags,
CI's prebuild step; lint/format/typecheck stripped; falls back to the `test`
script, then plain `vitest run`) run **twice** with `--reporter=json`; if ~0
files pass (config-level signature), one retry with the alternate invocation,
both attempts stored — harvest uses the recorded invocation → coverage smoke on
5 size-stratified test files (median secs/file × n_files = projected harvest) →
`screen.jsonl`. The screen output IS the final list. **PASS = ≥90% of test files
green identically in both vitest runs** (`frac_green_both`); flaky files
(differing results) and consistently-failing files are excluded at harvest, not
repo-fatal — consistent failures are classified per file
(`network`/`dom`/`missing-build`/`missing-tool`/`other`) and reported so a generic
prebuild step can be evaluated. Repo-level rejects: `runner != vitest`,
`install_ok = false`, `frac_green_both < 0.9`, `vitest_s > 600`, coverage smoke
failed, or `proj_harvest_s > 5400` (90 min). Every row carries `sha`, `domain`,
image digest, node/pnpm versions.

## Candidate pool (~35 → screen decides final ~24)

| repo | ecosystem | shape | notes/risk |
|---|---|---|---|
| unjs/nitro | unjs | toolkit monorepo | big suite; screen may exclude |
| vuejs/pinia | vuejs | single pkg | clean vitest |
| vuejs/vitepress | vuejs | ssg | medium |
| pmndrs/jotai | dai-shi | single pkg | small-fast |
| pmndrs/valtio | dai-shi | single pkg | proxies; some DOM |
| TanStack/query | TanStack | monorepo | suite may exceed 10 min → screen |
| drizzle-team/drizzle-orm | drizzle | monorepo | db-less tests mostly |
| fabian-hiller/valibot | — | schema lib | clean vitest |
| arktypeio/arktype | — | schema lib | attest on vitest — screen decides |
| supermacro/neverthrow | — | result lib | small |
| antfu/unocss | antfu | engine+presets monorepo | many preset packages |
| antfu/unplugin | antfu | single pkg | bundler-agnostic |
| withastro/astro | astro | framework monorepo | may exceed cap → screen |
| sveltejs/svelte | svelte | framework | may exceed cap → screen |
| honojs/hono | — | http framework | runner check |
| unnoq/orpc | — | rpc monorepo | **exclude-from-trpc-folds** |
| hey-api/openapi-ts | hey-api | codegen | snapshot tests |
| openapi-ts/openapi-fetch | hey-api | fetch client | small |
| redis/node-redis | redis | client monorepo | mock-server tests |
| colinhacks/zod | — | schema lib | jest→vitest migration — screen |
| gvergnaud/ts-pattern | — | pattern matching | runner check |
| es-toolkit | toss | utility lib | clean vitest |
| unadlib/mutative | — | immer alternative | small |
| nanostores/nanostores | — | state lib | tiny |
| bluwy/superjson | — | serializer | small |
| Rich-Harris/devalue | — | serializer | small |
| capricorn86/happy-dom | — | DOM impl | medium |
| huntabyte/bits-ui | — | svelte components | medium |
| Saul-Mirone/milkdown | — | editor monorepo | prosemirror stack |
| radix-vue/radix-vue | — | vue components | medium |
| tinylibs/tinybench | — | benchmark lib | tiny — maybe too small |
| QwikDev/qwik | qwik | framework | likely exceeds cap → screen |

Ecosystem exclusions logged (cap reached): unjs/unstorage, unjs/ofetch, unjs/consola,
unjs/c12 (unjs full at h3+nitro); shikijs/shiki, vueuse/core (antfu full at 2); vuex
(vuejs full; superseded by pinia anyway).

## Pre-logged exclusion *patterns*

- Runner ≠ vitest: fastify (tap), express (mocha), nestjs (jest), rxjs (mocha),
  pino (tap), lru-cache (tap), kysely (node:test), elysia (bun:test), most
  sindresorhus packages (ava), nodejs/undici (its own).
- External deps: transformers.js (model downloads), vercel/ai (API keys), playwright suites.
- Toolchain build steps: rolldown/biome/oxc (rust), tauri (rust).
- Near-duplicates/forks of listed repos; third schema-validation lib beyond
  zod+valibot+arktype.
- Dogfooded tooling: vitest-dev/vitest itself (its own coverage infra = atypical).

## Pair universe (documented)

Labels exist only for functions **covered by ≥1 test at that snapshot** — a function
with zero coverage anywhere has no verifiable label signal, so it is excluded from
the universe entirely. Evaluation is therefore stated on the covered-anywhere
universe; a deployed model could score uncovered functions too, but there is no
label to check it against. File-level and function-level metrics both use this
universe.

## Storage / evaluation plan

```
data/covpred/repos/<org>__<name>/
  meta.json        {ecosystem, domain, repo, pinned_sha, node_image, image_digest,
                    node/pnpm versions, extractor_version, suite_wall_s, n_tests,
                    n_pairs, pos_rate, coverage_selectivity, c1_recall, residual_n}
  baseline.json    empty-test covered files (setup mask)
  pairs.jsonl.gz   same schema as h3/trpc (+ "weight" only if sampling ever used)
  signals.jsonl    mocks/dyn sidecars
  graphs.db        per-repo graph, pinned ts-morph
exclusions.jsonl   {repo, reason, stage} — every drop logged
screen.jsonl       raw screen output per candidate (rows tagged with cmd version)
```

**coverage_selectivity** = mean share of the suite covering a function (per repo) —
downstream value is selectivity-dependent (high on h3, ~0 on trpc), so P3 results
are always reported alongside it.

**Per-repo QA gate.** `c1_recall` and `residual_n` go in meta.json. Any repo with
C1 recall < 0.98 is QUARANTINED pending diagnosis — fix generic bug classes only,
never hand-patch a single repo; each extractor change is logged in DECISIONS with
the repo that triggered it (so far: multi-line export regex ← trpc; dyn-import
edges ← h3/happydom; workspace resolve ← trpc diagnosis).

**Full pairs preferred over sampling.** At ~1.2M pairs/repo the full universe is cheap;
capping negatives would distort within-test percentile features and per-function
metrics. Rule: within-test percentile features are computed on the FULL candidate
universe before any sampling; if sampling is ever kept for train-time speed, store
`weight` = universe/sampled and report per-function metrics only on full candidate
sets, with all metrics labelled raw vs reweighted.

## Footprint / disk policy (measured on h3+trpc)

| artifact | size |
|---|---|
| graphs.db | ~7 MB per snapshot (trpc: 30 MB / 4 snaps) |
| pairs.jsonl.gz | 3–10 MB |
| signals + meta + baseline | <1 MB |
| **kept per repo** | **~10–40 MB → ~1 GB for ~20 repos** |
| transient per repo (clone + node_modules + docker layer) | ~0.5–1 GB, deleted after artifacts saved |

Policy: screen/harvest processes ONE repo at a time — delete the clone,
`node_modules`, and Docker layers once graph+pairs+meta are saved; prune the shared
pnpm store at the end. Peak transient ≤ ~1 GB; total kept ~1 GB.

Snapshots: one pinned sha per repo; for h3/trpc reuse existing (52/4) and, if P2
runs, add 2–3 widely-spaced NEW snapshots rather than adjacent commits.
