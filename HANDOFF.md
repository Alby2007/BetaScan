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

### trpc — labelling in progress (PAUSED here)

- `data/trpc_pilot/*.json`, one record per commit, resumable (existing records are skipped).
- Done: 2 records under OLD config (8 mutants each): `aac35fbd…` (node22, 8K/0S),
  `8b649ad…` (node24, 4K/4S). Covering sets 13–85 tests — much denser than h3.
- In flight when paused: first NEW-config commit — 25 mutants × 25 distinct files,
  mutant stage ~6/25 done. That commit's record is absent → it will rerun on resume.
- Target: `--n 7 --per-commit 25` → ~141 mutants (16 + 125), ≥30 distinct files wanted;
  the two old parents only had 6 eligible files each — watch `n_src_files_eligible`.

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
python3 stages/m2_labeller/trpc/pilot.py targets_scope/full__trpc__trpc data/trpc_pilot --n 7 --per-commit 25
```

~1–1.25 h/commit on this machine (combined install+suite×2+coverage container, then a mutant
container). On completion check: killed count 100–150, `n_mutant_files` union ≥30,
`src_files_below_min_cov`/`mutants_below_min_cov` fields for the selection-effect audit.

## Next steps (agreed order)

1. When 3+ new parents land: report trpc `>10`-stratum oracle headroom; stop for review.
2. Build trpc `rows.jsonl` + `graphs.db` equivalents (extractor is repo-agnostic —
   check how `data/graphs.db` was made in `stages/`).
3. Run B3-A on trpc mutants with the IDENTICAL model+prompt (`stages/m3_baselines/b3_llm.py`,
   resumable, throttle ~6s/call; flash-lite free-tier quota is large — h3 did 380 calls).
4. M1: small regularised LightGBM ranker, grouped k-fold BY SOURCE FILE, repo-agnostic
   features only, history from earlier commits only. FREEZE features+hyperparameters
   before scoring trpc. Ablations: structure+lexical / +history / +B3-rank feature / B3-only.
   Bar: beat best of B3/B4/B7/B8 (B3-A ≈ B8: n95 ~11.8, recall@5 ~0.556).
5. After M1: stratified 60–100 mutant B3-A subsample with a stronger paid model; log cost.
6. Write-up caveats already logged: trpc round-robin weights files equally (not population rates);
   h3 is public code (possible LLM contamination); B3 used a lite free model (baseline likely
   underestimated).

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
