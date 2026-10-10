#!/bin/bash
# Step 3: scale h3, oversampling mutants whose line is covered by >10 tests. Resumable. Usage: scale_h3.sh N
cd "$(dirname "$0")/../.."; N=${1:-40}; S=stages/m2_labeller
for k in $(seq 1 $N); do
  python3 $S/harvest_commits.py targets/h3 data/m2b --n $k --seed 7 --skip-c --exclude-dir data/m2 2>>data/scale.log
  python3 $S/flake_log.py targets/h3 data/m2b data/flake_log_b.json --runs 2 2>>data/scale.log
  python3 $S/mutate_commits.py targets/h3 data/m2b data/m2b_mut --min-cov 11 --per-commit 8 --files-per-commit 6 --seed 7 2>>data/scale.log
done
