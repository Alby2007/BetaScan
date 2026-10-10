# ImpactNet (BetaScan)

Structure-aware test-impact prediction for TypeScript/Vitest repositories.

**Hypothesis under test:** given a code change, a model that sees the *structural neighbourhood* of
the change predicts which tests are affected better than (a) simple heuristics and (b) a diff-reading
LLM — at the same test-execution budget. Prediction granularity is the test **file**. Labels come
from mutation testing plus per-test coverage. A negative result is acceptable.

- Dev repo: [`unjs/h3`](https://github.com/unjs/h3) — analysis complete (52 parents, 664 mutants, 488 killed)
- Held-out repo: [`trpc/trpc`](https://github.com/trpc/trpc) — labelling in progress (`packages/{server,client}` sources)

## Status snapshot

h3 baselines are complete: a free-tier diff-reading LLM (B3-A, gemini-flash-lite) and a learning-free
RRF fusion of LLM + call-graph (B8) **statistically tie** at n95 ≈ 11.8, recall@5 ≈ 0.556 in the
`>10`-covering-tests stratum; the reverse-call-graph heuristic (B4) is just behind and is free and
deterministic. The bar for the learned model (M1) is best-of B3/B4/B7/B8. See
[docs/results.md](docs/results.md) and `data/m3_b3.md`.

trpc: pilot labeller mid-run (`data/trpc_pilot/`). Early `>10`-stratum signal looks similar
(oracle headroom GO on point estimates). See [docs/trpc.md](docs/trpc.md).

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
