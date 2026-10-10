#!/bin/bash
cd /Users/alby/Albyssystems/BetaDeploy
while pgrep -f "repo_verify/run.sh" >/dev/null; do sleep 20; done
for i in 1 2 3; do
  python3 stages/m0_runner/run_suite.py targets_scope/full__colinhacks__zod --out data/repo_verify/zod_run$i.json \
    --install "sed -i '/\"packageManager\"/d' package.json && pnpm install --no-frozen-lockfile" \
    --test "pnpm exec vitest run --reporter=json --outputFile=/tmp/vitest.json" 2> data/repo_verify/zod_run$i.err
  echo "zod run$i exit=$?" >> data/repo_verify/progress.log
done
