#!/usr/bin/env python3
"""M1 training on h3: small regularised GBM over per-(mutant,covering-test) features.
Grouped k-fold by source file (a mutant's tests never train for their own file).
Reports out-of-fold metrics on the >10 stratum (same metric defs as m3_baselines/evaluate.py),
ablations (no B3 stack, no B5b-style targeted features), feature importances, and writes the
frozen spec (features + hyperparams) + fitted model for later trpc scoring.
Usage: m1_train.py FEATURES.jsonl OUTDIR [--min-cov 11]"""
import argparse, collections, json, math, pickle, statistics
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold

ap = argparse.ArgumentParser(); ap.add_argument("features"); ap.add_argument("out")
ap.add_argument("--min-cov", type=int, default=11); ap.add_argument("--folds", type=int, default=5)
a = ap.parse_args()

FEATS_ALL = ["call_dist", "imp_dist", "direct_import", "lex_overlap", "lex_jaccard",
             "log_covsize", "covsize_rel", "targeted_lines", "targeted_rel",
             "fan_in_mut", "log_dur", "log_ncov", "has_b3", "b3_rank"]
PARAMS = {"max_iter": 150, "learning_rate": 0.05, "max_leaf_nodes": 15,
          "l2_regularization": 1.0, "random_state": 0}

rows = [json.loads(l) for l in open(a.features)]
rows = [r for r in rows if r["ncov"] >= a.min_cov]
changes = collections.defaultdict(list)
for r in rows: changes[r["change"]].append(r)
print(len(rows), "pairs;", len(changes), "mutants;", len({r["src_file"] for r in rows}), "src-file groups")

def metrics(order, by_t):
    cand = order; n = len(cand); pos = [i for i, t in enumerate(cand) if by_t[t]]
    if not pos or not n: return None
    res = {"recall@5": sum(p < 5 for p in pos) / len(pos),
           "APFD": 1 - sum(p + 1 for p in pos) / (n * len(pos)) + 1 / (2 * n) if n > 1 else 1.0,
           "n95": 0}
    need = math.ceil(.95 * len(pos)); seen = 0
    for i, t in enumerate(cand):
        seen += by_t[t]
        if seen >= need: res["n95"] = i + 1; break
    return res

def cv_scores(feats):
    X = np.array([[r["f"].get(f, math.nan) for f in feats] for r in rows])
    y = np.array([r["label"] for r in rows]); groups = np.array([r["src_file"] for r in rows])
    oof = np.full(len(rows), np.nan)
    for tr, te in GroupKFold(a.folds).split(X, y, groups):
        clf = HistGradientBoostingClassifier(**PARAMS).fit(X[tr], y[tr])
        oof[te] = clf.predict_proba(X[te])[:, 1]
    per = {}
    for i, r in enumerate(rows):
        if not math.isnan(oof[i]): per.setdefault(r["change"], []).append((r["test"], r["label"], oof[i]))
    ms = []
    for c, xs in per.items():
        by = {t: l for t, l, s in xs}
        order = [t for t, l, s in sorted(xs, key=lambda x: (-x[2], x[0]))]
        m = metrics(order, by)
        if m: ms.append(m)
    return {k: statistics.mean(m[k] for m in ms) for k in ms[0]}, len(ms)

for name, feats in [("full (with B3 stack)", FEATS_ALL),
                    ("no-B3", [f for f in FEATS_ALL if f not in ("has_b3", "b3_rank")]),
                    ("no-targeted (no B5b-style)", [f for f in FEATS_ALL if not f.startswith("targeted")]),
                    ("no-B3 no-targeted", [f for f in FEATS_ALL if f not in ("has_b3", "b3_rank") and not f.startswith("targeted")])]:
    m, n = cv_scores(feats)
    print(f"{name:30s} n={n}  n95 {m['n95']:.2f}  recall@5 {m['recall@5']:.3f}  APFD {m['APFD']:.3f}")

# final model on ALL h3 rows, frozen feature set (no-B3 variant is the repo-portable default)
FINAL = [f for f in FEATS_ALL if f not in ("has_b3", "b3_rank")]
X = np.array([[r["f"].get(f, math.nan) for f in FINAL] for r in rows]); y = np.array([r["label"] for r in rows])
clf = HistGradientBoostingClassifier(**PARAMS).fit(X, y)
spec = {"train_repo": "h3", "features": FINAL, "params": PARAMS, "model": "HistGradientBoostingClassifier",
        "sklearn": "1.7.2", "min_cov": a.min_cov, "folds": a.folds, "n_pairs": len(rows),
        "n_mutants": len(changes), "n_src_files": len({r["src_file"] for r in rows})}
import pathlib
out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
json.dump(spec, open(out / "m1_spec.json", "w"), indent=1)
pickle.dump(clf, open(out / "m1_h3.pkl", "wb"))
clf2 = HistGradientBoostingClassifier(**PARAMS).fit(np.array([[r["f"].get(f, math.nan) for f in FEATS_ALL] for r in rows]), y)
pickle.dump(clf2, open(out / "m1_h3_b3stack.pkl", "wb"))
print("wrote", out / "m1_spec.json", "and", out / "m1_h3.pkl", "(+ b3stack variant)")
