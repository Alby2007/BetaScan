# P2 repo selection proposal (for review — no collection started)

## Selection criteria (objective, logged)

In: TypeScript source, Vitest suite, public GitHub repo, `pnpm`/`npm`/`yarn` installable,
suite expected ≤ ~10 min wall, deterministic (no external services/keys/models), not a fork.
Out (logged with reason): non-Vitest runners (jest/mocha/ava/tap/bun:test/deno/node:test),
heavy external deps (playwright downloads, model weights, API keys), rust/go build steps,
likely >10 min suites, near-duplicates/forks.
Diversity axes: org (cap **2 repos per org**, h3+trpc already counted), size, architecture
(single-package vs monorepo vs framework vs library), domain.

## Proposed pool (~24)

| repo | org | shape | notes/risk |
|---|---|---|---|
| unjs/nitro | unjs (1/2) | toolkit monorepo | big suite; may exceed cap |
| unjs/unstorage | unjs (2/2) | single pkg + drivers | many driver variants |
| vuejs/pinia | vuejs (1/2) | single pkg | clean vitest |
| vueuse/core | vueuse | utility collection | large flat suite |
| pmndrs/jotai | pmndrs (1/2) | single pkg | small-fast |
| pmndrs/valtio | pmndrs (2/2) | single pkg | proxies; some DOM |
| TanStack/query | TanStack | monorepo | suite may exceed 10 min → log |
| drizzle-team/drizzle-orm | drizzle | monorepo | db-less tests mostly |
| fabian-hiller/valibot | valibot | schema lib | clean vitest |
| arktypeio/arktype | arktype | schema lib | uses attest on vitest — verify |
| supermacro/neverthrow | — | result lib | small |
| antfu/unocss | antfu (1/2) | engine+presets monorepo | many preset packages |
| antfu/unplugin | antfu (2/2) | single pkg | bundler-agnostic |
| shikijs/shiki | shikijs | highlighter monorepo | grammar data heavy |
| vuejs/vitepress | vuejs (2/2) | ssg | medium |
| withastro/astro | astro | framework monorepo | may exceed cap → log |
| sveltejs/svelte | svelte | framework | suite may exceed cap → log |
| honojs/hono | hono | http framework | verify vitest config |
| unnoq/orpc | orpc | rpc framework monorepo | trpc-adjacent — same domain as held-out trpc; flag |
| hey-api/openapi-ts | hey-api (1/2) | codegen | snapshot tests |
| openapi-ts/openapi-fetch | hey-api (2/2) | fetch client | small |
| redis/node-redis | redis | client monorepo | mock-server tests |
| colinhacks/zod | zod | schema lib | **verify runner** (jest historically; vitest in v4) |
| gvergnaud/ts-pattern | — | pattern matching | verify vitest |
| es-toolkit | toss | utility lib | clean vitest |
| unadlib/mutative | — | immer alternative | small |
| nanostores/nanostores | nanostores | state lib | tiny |
| tinylibs/tinybench | tinylibs | benchmark lib | tiny — maybe too small |
| bluwy/superjson | — | serializer | small |
| Rich-Harris/devalue | — | serializer | small |
| capricorn86/happy-dom | — | DOM impl | medium |
| huntabyte/bits-ui | — | svelte components | svelte5; medium |
| Saul-Mirone/milkdown | milkdown | editor monorepo | prosemirror stack |
| radix-vue/radix-vue | radix-vue | vue components | medium |
| QwikDev/qwik | qwik | framework | big; likely exceeds cap → log |

Stretch (include if pool thins): unjs/ofetch, unjs/consola, unjs/c12 (org alternates only —
cap 2 total unjs including alternates), effect-ts/effect (likely >90 min → exclusion).

## Pre-logged exclusion *patterns* (examples)

- Runner ≠ vitest: fastify (tap), express (mocha), nestjs (jest), rxjs (mocha),
  pino (tap), lru-cache (tap), kysely (node:test), elysia (bun:test), most
  sindresorhus packages (ava), nodejs/undici (its own).
- External deps: transformers.js (model downloads), vercel/ai (API keys), playwright suites.
- Toolchain build steps: rolldown/biome/oxc (rust), tauri (rust).
- Near-duplicates: second schema-validation lib beyond zod+valibot+arktype cap of the same niche; vuex (superseded by pinia — not a fork but same org/niche → counts toward caps).
- Dogfooded tooling: vitest-dev/vitest itself (its own coverage infra = atypical).

## Storage / sampling plan

```
data/covpred/repos/<org>__<name>/
  meta.json        {org, repo, pinned_sha, node_image, suite_wall_s, n_tests,
                    n_pairs, pos_rate, exclusions_log ref}
  baseline.json    empty-test covered files (setup mask)
  pairs.jsonl.gz   same schema as h3/trpc + "weight" field (default 1.0)
  signals.jsonl    mocks/dyn sidecars
  graph fragment   appended to a per-repo graphs.db (pinned ts-morph)
exclusions.jsonl   {repo, reason, stage} — every drop logged
```

If a repo's pair count exceeds ~1.2M, cap *negatives* per test at 500 (keep all
positives); set `weight` = universe_negatives/sampled_negatives for that test so AP
and precision can be reweighted. All reported metrics must state whether they are
raw or weight-reweighted.

Snapshots: one pinned sha per repo; for h3/trpc reuse existing (52/4) and, if P2
runs, add 2–3 widely-spaced NEW snapshots rather than adjacent commits.
