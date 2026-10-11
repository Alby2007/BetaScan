# Residual breakdown + C1 precision/recall

## causes (test, covered-file) pairs outside runtime closure

| cause | n |
|---|---|
| MISSING_EDGE | 337 |
| OTHER | 4 |

## examples

**OTHER**
- `6a70335e02 packages/client/src/internals/types.test.ts -> packages/client/src/internals/transformer.ts`
- `caee09deaa packages/client/src/internals/types.test.ts -> packages/client/src/internals/transformer.ts`
- `f476d39932 packages/client/src/internals/types.test.ts -> packages/client/src/internals/transformer.ts`
- `fd3350cdbe packages/client/src/internals/types.test.ts -> packages/client/src/internals/transformer.ts`
**MISSING_EDGE**
- `6a70335e02 packages/client/src/internals/types.test.ts -> packages/client/src/links/internals/httpUtils.ts`
- `6a70335e02 packages/client/src/internals/types.test.ts -> packages/server/src/unstable-core-do-not-import/rpc/codes.ts`
- `6a70335e02 packages/client/src/links/localLink.test.ts -> packages/server/src/unstable-core-do-not-import/rpc/codes.ts`
- `6a70335e02 packages/server/src/adapters/next-app-dir.test.ts -> packages/server/src/unstable-core-do-not-import/rpc/codes.ts`
- `6a70335e02 packages/server/src/adapters/node-http/incomingMessageToRequest.test.ts -> packages/server/src/unstable-core-do-not-import/rpc/codes.ts`
- `6a70335e02 packages/server/src/unstable-core-do-not-import/router.mergeRouters.test.ts -> packages/server/src/unstable-core-do-not-import/rpc/codes.ts`
- `6a70335e02 packages/server/src/unstable-core-do-not-import/router.test.ts -> packages/server/src/unstable-core-do-not-import/rpc/codes.ts`
- `6a70335e02 packages/server/src/unstable-core-do-not-import/stream/jsonl.test.ts -> packages/server/src/unstable-core-do-not-import/rpc/codes.ts`

## C1 runtime-closure classifier, function level

- precision 0.392 · recall 1.000 (tp=48301 fp=74991 fn=24)
