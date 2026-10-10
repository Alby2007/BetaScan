# M1: extractor
1. `node extract.mjs REPO [COMMIT] > graph.json` (ts-morph, uses repo tsconfig; no repo install needed for in-repo edges)
2. `python3 build_db.py graph.json out.db` -> SQLite `nodes`, `edges` (both carry `commit_hash`)
3. `python3 queries.py out.db importers FILE | callers NAME | tests-importing FILE`
Nodes: file, test_file, function (functions, methods, ctors, accessors, fn-valued consts), class, type (interface/alias/enum), module (external pkg).
Edges: imports, calls (incl. `new`), extends, implements, uses_type, defined_in. `covers` is added in M2.
Top-level calls are attributed to the file node. Overload signatures are skipped.
Setup: `npm install` in this dir.
