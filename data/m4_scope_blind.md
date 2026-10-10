commit 66cfb8a3: 74 test files total

| kind | file | test files reached | how |
|---|---|---|---|
| asset/fixture | test/assets/dummy.pdf | 1 | path string match |
| asset/fixture | test/assets/sample.json | 1 | path string match |
| build-output | dist/ (build artefact) | 2 | path string match, test/dist.test.ts, test/unit/cli.test.ts |
| config | .github/workflows/ci.yml | 74 | global (all tests run under it) |
| config | build.config.ts | 74 | global (all tests run under it) |
| config | package.json | 74 | global (all tests run under it) |
| config | pnpm-workspace.yaml | 74 | global (all tests run under it) |
| config | tsconfig.json | 74 | global (all tests run under it) |
| config | vitest.config.mjs | 74 | global (all tests run under it) |
| support-code | test/_setup.ts | 27 | import graph |
| support-code | test/rules/_fixture.ts | 4 | import graph |
| support-code | test/bench/bench.impl.ts | 1 | import graph |
| support-code | test/bench/input.ts | 1 | import graph |
| support-code | test/bench/_bundler.ts | 0 | import graph |
| support-code | test/bench/_rules-fixtures.ts | 0 | import graph |
| support-code | test/bench/bench.ts | 0 | import graph |
| support-code | test/bench/bundle-inspect.ts | 0 | import graph |
| support-code | test/bench/path.ts | 0 | import graph |
| support-code | test/bench/request-proxy.ts | 0 | import graph |
| support-code | test/bench/rules-bundle-inspect.ts | 0 | import graph |
| support-code | test/bench/session.ts | 0 | import graph |
| support-code | test/rules/_augment.ts | 0 | import graph |

support files with >=1 reaching test: 4 of 13
distinct test files reached by support/asset files (excluding config): 32
