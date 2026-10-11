# Data artifacts & schemas

Everything under `data/` is committed output (incl. the 44 MB `graphs.db` so h3 graphs need not be
re-extracted). Names in **bold** are load-bearing for the evaluator.

## h3 records

| Path | Producer | Contents |
|---|---|---|
| `data/m2/<C>.json`, `data/m2b/<C>.json` | `harvest_commits.py` | per real commit C: `{commit, parent, date, files_changed, diff, suite_P, suite_C, cov_P}` |
| `data/m2_mut/<P>.json`, `data/m2b_mut/<P>.json` | `mutate_commits.py` | `{parent, commit, date, mutants[]}` — keyed by **parent** |
| `data/flake_log.json`, `data/flake_log_b.json` | `flake_log.py` | `{P: {test_file: [status per clean run]}}` |
| `data/graphs.db` | `extract_graphs.py` | M1 graphs for all h3 parents (SQLite) |
| `data/mutant_rows.jsonl` | `build_mutant_dataset.py` | raw rows incl. unresolved |
| **`data/rows_clean.jsonl`** | `build_mutant_dataset.py` | analysis rows (unresolved dropped) |
| **`data/rows_worst.jsonl`** | `--worst-case` | unresolved counted as worst-case kills |
| `data/b3/b3_{A,B}.jsonl` | `b3_llm.py` | `{change_id, model, variant, ranking[], n_tests, raw}` |
| `data/b3/SYSTEM_PROMPT.txt`, `prompt_*` | — | exact prompt + samples |
| `data/m3_b3.md` | `evaluate.py` | full h3 results tables |
| `data/trpc_pilot/` | `trpc/pilot.py` | trpc records (below) |

### m2 record (`data/m2/<C>.json`)

```jsonc
{
  "commit": "<C sha>", "parent": "<P sha>", "date": "ISO",
  "files_changed": ["src/x.ts", ...], "diff": "unified diff text",
  "suite_P": {"files": {"test/app.test.ts": {"status": "pass", "tests": 68, "failed": 0, "duration_ms": 793}}},
  "suite_C": {...},                       // same shape at C (absent when harvested --skip-c)
  "cov_P": {"commit": P, "wall_s": 300.0,
            "tests": {"test/app.test.ts": {"exit": 0, "secs": 3,
                                           "covered": {"src/x.ts": [10,11,12, ...]}}}}
}
```

### mutant record (`data/m2*_mut/<P>.json`)

```jsonc
{"parent": P, "commit": C, "date": "ISO",
 "mutants": [{"id": "src/x.ts:1234:BinaryOp", "file": "src/x.ts", "mutator": "BinaryOp",
              "line": 57, "original": "a === b", "replacement": "a !== b",
              "tests": ["test/a.test.ts", ...],       // covering tests at P
              "status": "Killed|Survived|Error|Flaky",
              "killed_by_files": ["test/a.test.ts"],  // failing in BOTH runs
              "secs": 12.3, "via": "split-timeout"?}]}
```

### trpc record (`data/trpc_pilot/<C>.json`)

Same idea, one file per **commit** (mutants inline). New-config records additionally carry
`suite_P`/`cov_P` in the h3 shape (green = pass in BOTH suite runs → `suite_P.files[t].status`),
plus audit fields `n_src_files_eligible`, `src_files_below_min_cov`, `mutants_below_min_cov`,
`n_mutant_files`, `excluded_files`, `image`, `stages`, `stage_times`. The two old-config records
and the first new-config one lack `suite_P`/`cov_P` — `build_rows.py` tolerates that
(`dur_ms=0`, no `covsize`).

### rows (`rows_*.jsonl`, one JSON object per line)

```jsonc
{"change_id": "<P[:10]>:<mutant id>", "kind": "mutant", "parent": P, "date": "ISO",
 "src_file": "src/x.ts", "mutator": "CondTrue", "line": 40,
 "test_file": "test/app.test.ts", "covers": 0|1, "fails": 0|1,
 "dur_ms": 543, "unresolved": 0|1}
```

One row per (mutant × green test file). `covers` = the test executed the mutated line at P;
`fails` = test satisfies the kill rule. `fails ⊆ covers` by construction.

### graphs.db

```sql
nodes(commit_hash, id, kind, name, file, start_line, end_line, exported, PRIMARY KEY(commit_hash,id))
edges(commit_hash, type, src, dst)   -- indexed (commit_hash,type,src) and (commit_hash,type,dst)
```

`id` shapes: `file:path`, `function:path#name`, `class:path#name`, `type:path#name`,
`module:pkg`. Edges: `imports`, `calls`, `extends`, `implements`, `uses_type`, `defined_in`.

### covpred pairs (`data/covpred/pairs_<repo>.jsonl.gz`, one JSON per line)

Function-level coverage labels for Phase 2. Built by `stages/p2_covpred/pairs.py`
from persisted `cov_P` coverage + the graph DB. Raw `.jsonl` is gitignored (size);
committed files are gzipped.

```json
{"repo":"h3","snapshot":"<commit>","test":"<test file path>",
 "func":"function:<file>#<name>","file":"<func's file>",
 "start":<int>,"end":<int>,
 "covered":<0|1>,           -- 1 iff >=1 line of [start,end] executed by the test
 "line_frac":<0..1>,        -- fraction of function lines executed
 "hits":<int>,"exec_lines":<int>}
```

Universe: functions in non-test files covered by >=1 green test at that snapshot
(files never covered by any test are excluded -- no executable evidence).
Excluded: non-green tests (suite_P pass only), test files as targets,
baseline/setup-covered lines (`baseline_<repo>.json` -- empty on h3/trpc).
Per-test sidecar `pairs_<repo>_signals.jsonl`: `mocks` (vi/jest.mock specs) and
`dyn` (import() specs) per test file. Type-only imports are recomputed from
`git show` at use time (heuristics.py).

## Logs / audits

`data/flake_log*.json` clean-run statuses · `data/shortcut_check*.json` non-covering-failure
probe · `data/b3_b4_overlap_detail.json` · `data/repo_verify/` trpc+zod suite screens ·
`data/m4_scope_blind.md`, `data/scope_repos.md` scoping reports · `data/h3*.json` M0 snapshots ·
`data/*.log` run logs.
