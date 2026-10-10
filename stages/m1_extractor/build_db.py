#!/usr/bin/env python3
"""graph.json (from extract.mjs) -> SQLite with `nodes` and `edges` tables (rows carry commit)."""
import json, sqlite3, sys
src, db = sys.argv[1], sys.argv[2]
g = json.load(open(src)); c = g["commit"] or "WORKTREE"
con = sqlite3.connect(db)
con.executescript("""
CREATE TABLE IF NOT EXISTS nodes(commit_hash TEXT, id TEXT, kind TEXT, name TEXT, file TEXT, start_line INT, end_line INT, exported INT, PRIMARY KEY(commit_hash,id));
CREATE TABLE IF NOT EXISTS edges(commit_hash TEXT, type TEXT, src TEXT, dst TEXT);
CREATE INDEX IF NOT EXISTS e_src ON edges(commit_hash,type,src); CREATE INDEX IF NOT EXISTS e_dst ON edges(commit_hash,type,dst);""")
con.execute("DELETE FROM nodes WHERE commit_hash=?", (c,)); con.execute("DELETE FROM edges WHERE commit_hash=?", (c,))
con.executemany("INSERT INTO nodes VALUES(?,?,?,?,?,?,?,?)", [(c, n["id"], n["kind"], n["name"], n["file"], n["start"], n["end"], int(n["exported"])) for n in g["nodes"]])
con.executemany("INSERT INTO edges VALUES(?,?,?,?)", [(c, e["type"], e["src"], e["dst"]) for e in g["edges"]])
con.commit(); print(c, len(g["nodes"]), "nodes", len(g["edges"]), "edges")
