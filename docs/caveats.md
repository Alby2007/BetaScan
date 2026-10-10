# Caveats & limitations

Everything here is also in `DECISIONS.md` (the authoritative log); this is the consolidated list.

## Labelling shortcut

`fails ⊆ covers` **by construction** — mutants are only run against tests that cover the mutated
line at P. A non-covering test that really fails (shared state, fixtures, config, mocks,
subprocesses) would be mislabelled as passing — which can only *flatter* structure rankers.

- Population probe (random mutants): 36, 0 violations → rule-of-three 95% upper bound ≈ 8.3%
- Worst-case probe (risk-targeted hub/top-level mutants): 60, 0 confirmed violations (1 transient
  flake)
- Holds **on h3 for mutants**; must be re-audited per repo (suites with heavy
  subprocess/snapshot/shared-state could break it). Not applicable to real commits — those used
  full-suite runs.

Consequences: coverage baselines are near-perfect on recall by construction — evaluation lives
**inside** the covering set (n95, APFD, time-fraction), which is the honest comparison.

## Coverage-blind stratum is thin

On h3 only ~5 informative non-src files reach tests (plus 6 config files affecting all tests —
nothing to rank). The stratum where B5 is undefined cannot carry a statistical claim on h3 alone.
Real commits there: 3/12, 0 failing labels.

## Sample sizes / clustering

Effective n is the cluster count, not the mutant count — h3 `>10`: 280 mutants but 51 commits /
39 files / 89 functions. h3 `>10` sampling only drew lines covered by ≥11 tests, so stratum sizes
are **not** population frequencies. trpc round-robin weights files equally — ranking-quality
measures, not population rates.

## LLM baseline caveats

- `gemini-3.5-flash-lite` is a weak free-tier model — a frontier model likely does better
  (bias runs *against* the structure hypothesis; B3 is probably underestimated).
- h3 is public code — possible training contamination (mutants themselves are novel).
- Free-tier quotas found: ~20 req/day per flash-class name; flash-lite has a much larger quota
  (380 calls in <1h).

## Toolchain gaps

- Stryker was abandoned: Stryker 10 + vitest-runner on Vitest 5/TS7 reported everything Survived
  even for trivially breaking mutants → custom ts-morph harness (`unused_stryker_mutate.py` kept
  for reference).
- Extractor: dynamic `import()` and calls through `any` are unresolved; tsconfig without test
  dirs → 0 test_file nodes.
- Type-only changes produce empty `covers` by design (no runtime lines) — a class where
  `uses_type` edges may carry signal coverage cannot.
- trpc CI failures on main are partly flake/environment/typecheck — real-failure stratum looked
  small (~8 candidates) and PR-branch failures need a GitHub token to classify.

## Flaky-test hygiene

Kill = green in all clean runs AND failing in both mutant runs. h3's two flaky/baseline-failing
files (`test/utils.test.ts`, `test/rules/match.test.ts`) are excluded per-parent; trpc's
`websockets.test.ts` likewise. Zero kill-rule violations found in the h3 audit.
