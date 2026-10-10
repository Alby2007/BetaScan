#!/bin/bash
cd /Users/alby/Albyssystems/BetaDeploy
for r in colinhacks__zod trpc__trpc; do
  for i in 1 2 3; do
    python3 stages/m0_runner/run_suite.py targets_scope/full__$r --out data/repo_verify/${r}_run$i.json \
      --install "COREPACK_ENABLE_STRICT=0 pnpm install --frozen-lockfile" \
      --test "COREPACK_ENABLE_STRICT=0 pnpm exec vitest run --reporter=json --outputFile=/tmp/vitest.json" 2> data/repo_verify/${r}_run$i.err
    echo "$r run$i exit=$?" >> data/repo_verify/progress.log
  done
done
