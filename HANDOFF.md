# HANDOFF — ImpactNet (structure-aware test-impact prediction)

Snapshot taken mid-run. The trpc labeller was paused cleanly; resuming is automatic (see below).

## What this project is

Hypothesis under test: *given a code change, a model that sees the structural neighbourhood of the
change predicts which tests are affected better than (a) simple heuristics and (b) a diff-reading LLM,
at the same test-execution budget.* Test-file-level prediction, TypeScript repos (Jest/Vitest).
Labels come from mutation testing + per-test coverage. A negative result is acceptable.

Dev repo: `unjs/h3` (all analysis so far). Held-out repo in progress: `trpc/trpc`
(packages/{server,client} only). Read `DECISIONS.md` first — every design decision, model identity,
caveat and pre-registered criterion is logged there.

## Current state

### h3 — analysis complete

- 52 parent commits, 664 mutants, 488 killed; 280 mutants in the ">10 covering tests" stratum.
- Graph: `data/graphs.db` (44M SQLite, nodes+edges per commit: imports/calls/extends/implements/uses_type).
- Rows: `data/rows_clean.jsonl` (clean), `data/rows_worst.jsonl` (unresolved-mutant sensitivity bound).
- Go/no-go PASSED: oracle n95/ncov 0.417 < 0.5, B5a 0.796 > 0.7 (commit-clustered CIs).

Baseline results, `>10` stratum (n=280), covering-set ranking:

| Ranker | n95 | recall@5 | APFD |
|---|---|---|---|
| Oracle | 7.90 | 0.746 | 0.789 |
| B3-A LLM (gemini-flash-lite, diff+paths) | 11.89 | 0.556 | 0.682 |
| B8 RRF(B3,B4) — free fusion | 11.84 | 0.554 | 0.683 |
| B4 reverse call-graph | 12.71 | 0.497 | 0.649 |
| B7 lexical overlap | 14.74 | 0.426 | 0.594 |
| B5a coverage-random | 17.05 | 0.264 | 0.501 |

Paired diffs (commit-clustered): B8 beats B4 (n95 −0.87, r5 +0.056, APFD +0.034, all CIs excl. 0);
**B8 statistically TIES B3-A on every metric.** Earlier "B3/B4 complementary" claim was corrected:
union-of-top-5s finds *fewer* failing tests than best top-10 (budget artifact). M1 bar =
best of B3/B4/B7/B8 → effectively B3-A ≈ B8. B4 stays reported separately (free, deterministic).

Full tables + all clusterings: `data/m3_b3.md`. B3 logs: `data/b3/` (model `gemini-flash-lite-latest`,
served `gemini-3.5-flash-lite`, temp 0, 380 calls, 0 parse failures; prompt in `data/b3/SYSTEM_PROMPT.txt`).

### trpc — labelled, augmented, baselined; scored set FROZEN

- `data/trpc_pilot/*.json`, one record per commit, resumable (existing records are skipped).
- DONE + augmented: 241 mutants total, 233 clean / 184 killed, 63 distinct src files
  (augment added mutants but few NEW files — same ~68 eligible files exist per parent).
  Rows `data/trpc_rows{,_worst}.jsonl`, graphs `data/trpc_graphs.db`, eval `data/trpc_eval.md`.
- **FROZEN scored set**: `data/m1/trpc_ids_frozen.json` (233 change_ids, sha256 `ec4ecc72`).
  Scored subset = killed + >10 covering tests; M1 scored on it ONCE.
- Go/no-go GO (clean + worst-case). Ordering FLIPS vs h3: **B4 is the bar** (n95 28.88),
  B8 ties it (27.92), B3-A worse (+1.96 [+0.17,+3.84]).
- Edge-type ablation: imports carry most of B4 (B1 = 86% of n95 gain; calls-only B4c = 35%);
  calls add ~+1 n95 unit. Controlled miss analysis (`--max-frac 0.5`): registration-layer
  hypothesis survives control — see `data/b4_misses.md`.
- Regeneration integrity: 176 verify byte-identical, 0 mismatches, 15 non-regenerable
  (all in the 2 old-config records).
- B3-A coverage 117/184 killed. Resumed run filling the ~67 remainder after a Gemini
  500/day quota window; new records log `served_model` (first 117 predate the field).

### M1 — trained on h3, FROZEN (not yet scored on trpc)

- sklearn HistGradientBoostingClassifier (LightGBM has no cp314 wheels), 12 repo-agnostic
  features, GroupKFold(5) by src_file. Spec `data/m1/m1_spec.json`; models `data/m1/m1_h3{,_b3stack}.pkl`.
- Features/graphs versioned: ts-morph pinned 28.0.0; h3 re-extracted → `data/graphs_v28_h3.db`.
- h3 grouped-CV: no-B3 ≈ B4 (12.59/0.494/0.641); +B3-stack below B3-A (11.62/0.533/0.663).
- Pre-registered tiers (DECISIONS.md, precedence): WIN (paired n95 CI excl. 0 for M1) →
  LOSS (CI excl. 0 against) → MATCH (CI inside ±10% of bar's n95) → INCONCLUSIVE.
  Bar = best baseline per repo by rule → **trpc bar is B4**. Frozen artifacts hashed:
  m1_h3.pkl `758def7e`, b3stack `947b9ddd`, spec `f3f687db`. Real file-cluster count 59
  → paired-CI hw ~2.12 vs MATCH margin ±2.89.

## What is NOT in this repo (restore on the PC)

1. **Target clones** (gitignored, just re-clone):
   - `targets/h3` — `git clone https://github.com/unjs/h3 targets/h3`
   - `targets_scope/full__trpc__trpc` — `git clone https://github.com/trpc/trpc targets_scope/full__trpc__trpc`
   (pilot.py uses their git history; the working tree state doesn't matter.)
2. **`.secrets/gemini_key`** — Gemini API key for B3. Copy manually; never commit.
3. **Docker images** — rebuild from `docker/`:
   ```
   docker build -f docker/Dockerfile        -t impactnet-node    docker/   # node24 era
   docker build -f docker/Dockerfile.node22 -t impactnet-node22  docker/   # node22 era
   ```
   Era routing is automatic via each commit's `engines.node` (`image_for()` in pilot.py).
4. **Docker volumes** `impactnet-pnpm-store`, `impactnet-root-cache` — auto-created;
   they just make repeat installs faster (cold on first run).
5. **`ts-morph` for the mutator** — `stages/m2_labeller/node_modules` is a committed symlink to
   `stages/m1_extractor/node_modules`; run `cd stages/m1_extractor && npm install` once
   (package-lock committed) so the symlink resolves.
6. Python 3.14 used; deps are stdlib-only for the stages below (mutation harness needs node inside docker).

## Resume

```
python3 stages/m2_labeller/trpc/pilot.py targets_scope/full__trpc__trpc data/trpc_pilot --augment 25
```

Augment is resumable per record (`augmented` field). Then:

```
python3 stages/m2_labeller/trpc/build_rows.py targets_scope/full__trpc__trpc data/trpc_pilot data/trpc_rows.jsonl
python3 stages/m2_labeller/trpc/build_rows.py targets_scope/full__trpc__trpc data/trpc_pilot data/trpc_rows_worst.jsonl --worst-case
python3 stages/m3_baselines/b3_llm.py data/trpc_rows.jsonl data/trpc_graphs.db targets_scope/full__trpc__trpc data/trpc_b3 \
  --variant A --provider gemini --model gemini-flash-lite-latest --mutdirs data/trpc_pilot --sleep 7   # GEMINI_API_KEY env
python3 stages/m3_baselines/evaluate.py data/trpc_rows.jsonl data/trpc_graphs.db data/trpc_eval --m2dir data/trpc_pilot --b3dir data/trpc_b3
```

## Next steps (agreed order)

1. B3-A delta completes (~67 calls, running) → re-eval → report final table + file-clustered
   paired CIs (B3-A vs B4, B8 vs B4) and served-model split (first 117 have no field).
2. **STOP for review before scoring M1 on trpc** (features/hyperparams frozen, artifacts hashed;
   nothing about M1 may be tuned against trpc numbers).
3. Score M1 (h3-trained, frozen) on trpc → report vs pre-registered WIN/MATCH/LOSS tiers;
   report B5b-style `targeted_*` features separately (sign unstable across repos).
4. Reverse direction: train trpc → test h3, secondary check (trpc is small; weaker evidence).
5. Stronger-model B3 rerun on a trpc subsample (prompts persisted; use explicit versioned
   model name; also measures alias drift vs the saved flash-lite rankings).
6. Write-up caveats already logged: trpc round-robin weights files equally (not population rates);
   both repos public (LLM contamination possible; hurts B3, not structure); B3 = lite free model.

## Key paths

| Path | What |
|---|---|
| `stages/m2_labeller/trpc/pilot.py` | trpc end-to-end labeller (suite×2, per-file coverage, mutants) |
| `stages/m2_labeller/trpc/run_mutants.mjs` | ts-morph mutator harness (same operators as h3) |
| `stages/m2_labeller/coverage_per_test.py` | h3 per-test coverage |
| `stages/m3_baselines/evaluate.py` | all baselines B0–B8 + clustered CIs (run: `--m2dir data/m2,data/m2b`) |
| `stages/m3_baselines/b3_llm.py` | B3 runner (resumable JSONL) |
| `stages/m3_baselines/b3_b4_overlap.py` | overlap/complementarity analysis |
| `data/m3_b3.md` | full h3 results |
| `DECISIONS.md` | decision log — read this |

## Gotchas

- trpc tests: pnpm only, run from repo root, `--watch false` (see `.cursor/rules` in the clone).
- `websockets.test.ts` is flaky at trpc HEAD — excluded per-parent via green-file detection.
- Old-config records lack the new logging fields; fine for labels, just not for the audit stats.
- `data/graphs.db` is 44M — committed so the PC doesn't need to re-extract h3 graphs.
- Gemini key must stay in `.secrets/` (gitignored). B3 sends only public-repo code.
