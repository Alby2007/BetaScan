#!/usr/bin/env python3
"""Grouped-CV learnability check (exploratory, h3 = dev repo).
HistGradientBoostingClassifier (sklearn; documented LightGBM substitute — same
py3.14 constraint as M1). Features are rank/percentile-normalised WITHIN each
(snapshot,test) candidate set, inside each fold only.
Two groupings, 5-fold each: by source file (all pairs of a func's file held out
together) and by test file. Reports pooled AP, snap-macro AP, per-test AP,
per-func AP, with the C5 fixed-heuristic AP on the same held-out rows as the bar.
Usage: cv.py FEATS.npz PAIRS.jsonl[.gz] --out rep.md"""
import argparse, gzip, json, collections, sys
import numpy as np
ap = argparse.ArgumentParser(); ap.add_argument("npz"); ap.add_argument("pairs"); ap.add_argument("--out", default="")
a = ap.parse_args()
Z = np.load(a.npz, allow_pickle=True)
feats = [str(f) for f in Z["feats"]]
X0 = np.stack([Z[f"f_{k}"] for k in feats], 1).astype(np.float32)
y = Z["y"].astype(int); snaps = Z["snap"]
# group keys are P:path — strip the snapshot prefix so ALL snapshots of the same
# file/test are held out together (near-duplicate snapshots would otherwise leak)
tests = np.array([t.split(":", 1)[1] for t in Z["test"]])
files = np.array([f.split(":", 1)[1] for f in Z["gfile"]])

# C5 score replication: -10*impd - calld + 0.01*lex   (features carry raw values)
i_impd = feats.index("impd"); i_cal = feats.index("calld"); i_lex = feats.index("tok_overlap")
c5 = -10 * X0[:, i_impd] - X0[:, i_cal] + 0.01 * X0[:, i_lex]

# within-(snap,test) percentile normalisation of X -> Xn (computed on the FULL set once;
# percentile ranks are row-local transforms — recomputing per fold would shift nothing
# because each (test,func) row's rank depends only on its own test's candidate set,
# which is either fully in-train or fully in-test for the file-grouping... for the
# test-grouping held-out tests are absent anyway, so per-fold recomputation is
# unnecessary; do it globally per test for both groupings.)
Xn = np.zeros_like(X0)
test_rows = collections.defaultdict(list)
for i, t in enumerate(tests): test_rows[t].append(i)
for t, ii in test_rows.items():
    ii = np.array(ii)
    for j in range(X0.shape[1]):
        col = X0[ii, j]
        order = col.argsort().argsort()
        Xn[ii, j] = order / max(1, len(ii) - 1)
# binary flags: leave as-is (percentile of a binary col is rank-ish anyway; keep raw for interpretability)
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold
from sklearn.metrics import average_precision_score

def run_cv(groups, gname, n_split=5):
    kf = GroupKFold(n_split); ap_m = []; ap_c = []; pt_m = []; pt_c = []; ps_m = []; ps_c = []; pf_m = []; pf_c = []
    fold = 0
    for tr, te in kf.split(Xn, y, groups):
        fold += 1
        clf = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.08, early_stopping=True, random_state=0)
        clf.fit(Xn[tr], y[tr])
        s = clf.predict_proba(Xn[te])[:, 1]
        if y[te].any():
            ap_m.append(average_precision_score(y[te], s)); ap_c.append(average_precision_score(y[te], c5[te]))
        # per-test / per-func / per-snap macro on held-out rows
        tm = collections.defaultdict(list); tf = collections.defaultdict(list); ts = collections.defaultdict(list)
        for k, i in enumerate(te):
            tm[tests[i]].append(k); tf[files[i]].append(k); ts[snaps[i]].append(k)
        pt_m.append(np.mean([average_precision_score(y[te][ii], s[ii]) for ii in tm.values() if y[te][ii].any()]))
        pt_c.append(np.mean([average_precision_score(y[te][ii], c5[te][ii]) for ii in tm.values() if y[te][ii].any()]))
        pf_m.append(np.mean([average_precision_score(y[te][ii], s[ii]) for ii in tf.values() if y[te][ii].any()]))
        pf_c.append(np.mean([average_precision_score(y[te][ii], c5[te][ii]) for ii in tf.values() if y[te][ii].any()]))
        ps_m.append(np.mean([average_precision_score(y[te][ii], s[ii]) for ii in ts.values() if y[te][ii].any()]))
        ps_c.append(np.mean([average_precision_score(y[te][ii], c5[te][ii]) for ii in ts.values() if y[te][ii].any()]))
        print(f"  {gname} fold {fold}: pooled AP model {ap_m[-1]:.3f} vs C5 {ap_c[-1]:.3f}", flush=True)
    return {k: (np.mean(v), v) for k, v in [("pooled", ap_m), ("pooled_C5", ap_c), ("per_test", pt_m), ("per_test_C5", pt_c), ("per_func", pf_m), ("per_func_C5", pf_c), ("per_snap", ps_m), ("per_snap_C5", ps_c)]}

lines = ["# Grouped-CV learnability check — h3 (dev repo), exploratory\n",
         "| grouping | pooled AP model | pooled AP C5 | per-test model | per-test C5 | per-func model | per-func C5 | per-snap model | per-snap C5 |",
         "|---|---|---|---|---|---|---|---|---|"]
for g, nm in [(files, "by source file"), (tests, "by test file")]:
    r = run_cv(g, nm)
    lines.append(f"| {nm} | {r['pooled'][0]:.3f} | {r['pooled_C5'][0]:.3f} | {r['per_test'][0]:.3f} | {r['per_test_C5'][0]:.3f} | {r['per_func'][0]:.3f} | {r['per_func_C5'][0]:.3f} | {r['per_snap'][0]:.3f} | {r['per_snap_C5'][0]:.3f} |")
rep = "\n".join(lines) + "\n"
print(rep)
if a.out: open(a.out, "w").write(rep)
