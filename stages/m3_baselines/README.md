# M3: baselines + evaluator
1. `python3 extract_graphs.py REPO MUTDIR data/graphs.db`  (M1 extractor at every parent commit)
2. `python3 evaluate.py data/mutant_rows.jsonl data/graphs.db data/m3_results`  -> `data/m3_results.md`
Rankers (all use only the parent commit P: graph at P, coverage at P, history from earlier parents):
- B0 random. B1 import-proximity (reverse-import BFS distance from the changed file). B2 history co-failure (per-file, then per-dir, then global rate, trained on the 8 earliest parents).
- B4 reverse-call reachability: locate the mutated function (innermost function node containing the line), BFS over reversed `calls` edges, test rank = hops to any node in the test file; ties broken by import distance.
- B5 family (EXTRA, not in the plan; dynamic coverage selection, coverage at P): B5a covering tests first in random order; B5b covering tests, most targeted first (fewest total covered lines); B5c covering tests, ordered by historical failure rate (trained on earlier parents). M1 must beat the best of B5a/b/c. fails is a subset of covers on mutants by physics (a test can only catch a mutant on a line it executes), so recall cannot show structure beating coverage; the question is test count at 95% recall (`n95`, `n95_vs_B5`) and ranking inside the covering set.
- Lean on per-stratum rows: 102 of 256 killed mutants (40%) have exactly 1 covering test (trivial). The `cov>=2` bucket pools the non-trivial strata.
- `real_commit_strata.py`: real commits where B5 is undefined (config/build files touched, or no covering tests) are reported separately and never pooled with mutants. Currently 3/12 and none has a failing-test label, so nothing can be scored there yet.
- B3 (LLM) NOT implemented: model/API key not chosen yet.
Splits: temporal (last 4 parents = test); also a stricter view that drops test mutants whose src file appears in train. Random tie-breaks are averaged over 5 seeds.
Metrics: recall@k (1,3,5, 5/10/20% of candidates), hit@k, APFD, fraction of suite time needed to reach 95% recall of failing tests. Candidates: full suite, or covering tests only. Stratified by covering-set size (1, 2-3, 4-10, >10). Only killed mutants are scored.
