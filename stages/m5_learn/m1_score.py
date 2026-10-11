#!/usr/bin/env python3
"""M1 scoring on a held-out repo: load a trained pkl + a feature file, emit per-mutant test
rankings as b3_*.jsonl-shaped records so evaluate.py computes metrics + clustered paired CIs
with identical semantics. SCORE-ONCE: run only after review.
Usage: m1_score.py FEATURES.jsonl MODEL.pkl SPEC.json OUT.jsonl --variant NAME [--ids IDS.json] [--min-cov 11]"""
import argparse, collections, json, math, pickle
import numpy as np
ap = argparse.ArgumentParser(); ap.add_argument("features"); ap.add_argument("model"); ap.add_argument("spec"); ap.add_argument("out")
ap.add_argument("--variant", required=True); ap.add_argument("--ids", default=""); ap.add_argument("--min-cov", type=int, default=11)
a = ap.parse_args()
spec = json.load(open(a.spec)); feats = list(spec["features"])
clf = pickle.load(open(a.model, "rb"))
if getattr(clf, "n_features_in_", len(feats)) > len(feats):  # b3stack variant: trained on FINAL + has_b3 + b3_rank
    feats += ["has_b3", "b3_rank"]
frozen = set(json.load(open(a.ids))) if a.ids else None
pairs = collections.defaultdict(list)
for l in open(a.features):
    r = json.loads(l)
    if r["ncov"] < a.min_cov: continue
    if frozen and r["change"] not in frozen: continue
    pairs[r["change"]].append(r)
out = open(a.out, "w")
name = a.model.replace("\\", "/").split("/")[-1].replace(".pkl", "")
for c, rs in pairs.items():
    X = np.array([[r["f"].get(f, math.nan) for f in feats] for r in rs])
    s = clf.predict_proba(X)[:, 1]
    order = [r["test"] for r, _ in sorted(zip(rs, s), key=lambda x: (-x[1], x[0]["test"]))]
    out.write(json.dumps({"change_id": c, "variant": a.variant, "model": name, "ranking": order, "n_tests": len(order)}) + "\n")
print(len(pairs), "mutants scored ->", a.out)
