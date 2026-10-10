# M0: suite runner
`run_suite.py REPO [--commit SHA] [--out f.json]` archives the commit, runs install + Vitest
inside the `impactnet-node` Docker image (`docker/Dockerfile`, Node 24), and writes
`{commit, wall_s, files: {path: {status, tests, failed, duration_ms}}}`.
Build image: `docker build -t impactnet-node docker`. Non-Vitest repos: override `--install/--test`
(test must write JSON reporter output to /tmp/vitest.json).
