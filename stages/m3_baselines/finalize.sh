#!/bin/bash
# After scale_h3.sh: resolve hangs, rebuild labels (clean + worst case), graphs for new parents, evaluate both, then screen candidate repos.
cd "$(dirname "$0")/../.."; S=stages
python3 $S/m2_labeller/retry_timeouts.py targets/h3 data/m2_mut data/m2b_mut 2>>data/finalize.log
python3 $S/m2_labeller/build_mutant_dataset.py data/rows_clean.jsonl --pair data/m2:data/m2_mut --pair data/m2b:data/m2b_mut --flake data/flake_log.json --flake data/flake_log_b.json >>data/finalize.log 2>&1
python3 $S/m2_labeller/build_mutant_dataset.py data/rows_worst.jsonl --pair data/m2:data/m2_mut --pair data/m2b:data/m2b_mut --flake data/flake_log.json --flake data/flake_log_b.json --worst-case >>data/finalize.log 2>&1
python3 $S/m3_baselines/extract_graphs.py targets/h3 data/m2b_mut data/graphs.db >>data/finalize.log 2>&1
python3 $S/m3_baselines/evaluate.py data/rows_clean.jsonl data/graphs.db data/m3_final_clean --m2dir data/m2,data/m2b >>data/finalize.log 2>&1
python3 $S/m3_baselines/evaluate.py data/rows_worst.jsonl data/graphs.db data/m3_final_worst --m2dir data/m2,data/m2b >>data/finalize.log 2>&1
python3 $S/m4_scope/scope_repos.py data/scope_repos.md honojs/hono colinhacks/zod unjs/unstorage unjs/consola unjs/ofetch unjs/c12 trpc/trpc TanStack/query vuejs/pinia unjs/nitro >>data/finalize.log 2>&1
echo FINALIZE-DONE >>data/finalize.log
