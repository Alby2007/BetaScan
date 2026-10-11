# ImpactNet (BetaScan)

Structure-aware test-impact prediction for TypeScript/Vitest repositories.

**Hypothesis under test:** given a code change, a model that sees the *structural neighbourhood* of
the change predicts which tests are affected better than (a) simple heuristics and (b) a diff-reading
LLM — at the same test-execution budget. Prediction granularity is the test **file**. Labels come
from mutation testing plus per-test coverage. A negative result is acceptable.

- Dev repo: [`unjs/h3`](https://github.com/unjs/h3) — analysis complete (52 parents, 664 mutants, 488 killed)
- Held-out repo: [`trpc/trpc`](https://github.com/trpc/trpc) — labelling in progress (`packages/{server,client}` sources)

## Status snapshot

h3 baselines complete (`>10` stratum, 280 killed mutants): B3-A (gemini-flash-lite, n95 11.89) and
B8 RRF fusion (11.84) **statistically tie**; the B4 call-graph heuristic is just behind (12.71) and is
free and deterministic.

**trpc cross-repo result (the headline):** the ordering flips. On the frozen scored set
(233 mutants, 184 killed, `data/m1/trpc_ids_frozen.json`), **B4 is the best baseline** (n95 28.88),
B8 ties it (27.92), and B3-A is *worse* on n95 (29.88, paired diff +1.96 [+0.17,+3.84]). A lite
diff-reading LLM helped on h3 but adds nothing beyond B4 on trpc — the call/import-graph heuristic
is the only ranker that is consistently strong on both repos.

Edge-type ablation (both repos): B4's signal is mostly **import distance** (B1 alone captures
~86% of B4's n95 gain on trpc, ~74% on h3); call edges add a modest but significant increment.
Controlled error analysis (`--max-frac 0.5`): B4 misses concentrate in registration/indirection
layers — hypothesis, not yet proven. See `data/b4_misses.md`.

**State:** trpc scored set frozen (sha256 `ec4ecc72`); M1 trained on h3 and frozen
(`data/m1/m1_h3.pkl` + spec, hashes in `DECISIONS.md`). B3-A trpc coverage 117/184 — the remainder
awaits a Gemini free-tier quota window (~500/day); a resumable run completes it, then evaluation
re-runs and the pipeline **stops for review before M1 is scored on trpc** (score-once rule).

## Layout

```
stages/            pipeline stages (each has a README/docstring)
  m0_runner/       Vitest suite runner in Docker -> per-test-file pass/fail JSON
  m1_extractor/    ts-morph static graph extractor -> graph.json -> SQLite (graphs.db)
  m2_labeller/     harvest commits, per-test coverage, mutation labelling
    trpc/          trpc end-to-end pilot (suites+coverage+mutants per commit)
  m3_baselines/    B0-B8 rankers + evaluator (commit/file/function-clustered CIs)
  m4_scope/        coverage-blind scoping probes
docker/            impactnet-node (Node 24) / impactnet-node22 images
data/              harvested records, rows.jsonl, graphs.db, b3 logs, result tables
targets/           h3 clone (gitignored, re-clone)
targets_scope/     trpc clone (gitignored, re-clone)
.secrets/          API keys (gitignored, never commit)
```

## Docs

| Doc | Contents |
|---|---|
| [docs/setup.md](docs/setup.md) | environment, Docker images/volumes, secrets, Windows notes |
| [docs/pipeline.md](docs/pipeline.md) | stage-by-stage walkthrough with commands |
| [docs/data.md](docs/data.md) | artifact inventory + record/rows/graphs.db schemas |
| [docs/baselines.md](docs/baselines.md) | B0–B8 definitions, metrics, evaluation mechanics |
| [docs/results.md](docs/results.md) | h3 results + trpc status snapshot |
| [docs/trpc.md](docs/trpc.md) | trpc scope, era routing, config differences vs h3 |
| [docs/caveats.md](docs/caveats.md) | known limitations and biases |

`DECISIONS.md` is the authoritative decision log — every design decision, model identity, caveat
and pre-registered criterion. `HANDOFF.md` is the mid-run snapshot with resume instructions.

## Quickstart (research pipeline, not an app)

```bash
# setup (once)
git clone https://github.com/unjs/h3 targets/h3
git clone https://github.com/trpc/trpc targets_scope/full__trpc__trpc
cd stages/m1_extractor && npm install && cd -
docker build -f docker/Dockerfile        -t impactnet-node    docker/
docker build -f docker/Dockerfile.node22 -t impactnet-node22  docker/

# trpc labeller (resumable; ~40-70 min/commit)
python stages/m2_labeller/trpc/pilot.py targets_scope/full__trpc__trpc data/trpc_pilot --n 7 --per-commit 25

# graphs + rows + evaluation
python stages/m3_baselines/extract_graphs.py targets_scope/full__trpc__trpc data/trpc_pilot data/trpc_graphs.db
python stages/m2_labeller/trpc/build_rows.py targets_scope/full__trpc__trpc data/trpc_pilot data/trpc_rows.jsonl
python stages/m3_baselines/evaluate.py data/trpc_rows.jsonl data/trpc_graphs.db data/trpc_eval \
    --m2dir data/trpc_pilot --b3dir data/trpc_b3
```

Requires: Python 3.13+, Node 24, Docker (Linux containers), pnpm inside containers only.
