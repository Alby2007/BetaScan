#!/usr/bin/env python3
"""queries.py DB importers FILE | callers FUNC | tests-importing FILE (transitive)"""
import sqlite3, sys
db, q, arg = sys.argv[1:4]
con = sqlite3.connect(db)
if q == "importers":
    r = con.execute("SELECT src FROM edges WHERE type='imports' AND dst=?", (f"file:{arg}",))
elif q == "callers":
    r = con.execute("SELECT e.src FROM edges e WHERE e.type='calls' AND e.dst IN (SELECT id FROM nodes WHERE name=?)", (arg,))
elif q == "tests-importing":
    r = con.execute("""WITH RECURSIVE up(id) AS (SELECT ? UNION SELECT e.src FROM edges e JOIN up ON e.dst=up.id WHERE e.type='imports')
                       SELECT up.id FROM up JOIN nodes n ON n.id=up.id WHERE n.kind='test_file'""", (f"file:{arg}",))
for (x,) in sorted(r): print(x)
