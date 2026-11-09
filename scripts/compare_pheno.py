"""One table for the A/B/C phenology-feature experiment, read from `geocrop cv-stability` outputs (runs nothing).

    python scripts/compare_pheno.py --dir out/pheno --atypical SOYBEAN_1 SOYBEAN_2 SOYBEAN_3

Expects <dir>/<group>_<A|B|C>/ with cv_stability.csv, confusion/ and watch_polygons.csv (all soybean polygons watched).
Writes PHENO_ABC.csv / .md and PHENO_ABC_other_polygons_changes.csv. Internal CV; a recommendation for human review.
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

T = ("maize", "soybean", "sunflower")


def prf(cm, c):
    tp = cm.loc[c, c]
    p, r = tp / max(cm[c].sum(), 1), tp / max(cm.loc[c].sum(), 1)
    return p, r, 2 * p * r / max(p + r, 1e-12)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--groups", nargs="+", default=["post_season", "in_season_d196", "in_season_d226"])
    ap.add_argument("--atypical", nargs="+", default=[])
    a = ap.parse_args()
    R = Path(a.dir)
    rows, flips, W = [], [], {}
    for g in a.groups:
        for s in "ABC":
            d = R / f"{g}_{s}"
            if not (d / "cv_stability.csv").exists():
                continue
            t = pd.read_csv(d / "cv_stability.csv")
            t = t[t.status == "ok"]
            w = pd.read_csv(d / "watch_polygons.csv")
            W[(g, s)] = w
            for kind in ("spatial_blocks", "polygon_stratified"):
                k, wk = t[t.kind == kind], w[w.kind == kind]
                if not len(k):
                    continue
                row = dict(group=g, set=s, cv=kind, partitions=len(k), OA=k.overall_accuracy.mean(),
                           macro_f1=k.macro_f1.mean(), target_macro_f1_px=k.target_macro_f1.mean(),
                           target_macro_f1_parcel=k.parcel_target_macro_f1.mean(), parcel_OA=k.parcel_overall_accuracy.mean())
                kap, pr = [], {c: [] for c in T}
                for v in k.variant:
                    cm = pd.read_csv(d / "confusion" / f"{v}.csv", index_col=0)
                    n = cm.values.sum()
                    po, pe = np.trace(cm.values) / n, (cm.sum(axis=1) * cm.sum(axis=0)).sum() / n ** 2
                    kap.append((po - pe) / (1 - pe))
                    for c in T:
                        pr[c].append(prf(cm, c))
                row["kappa"] = np.mean(kap)
                for c in T:
                    x = np.array(pr[c])
                    row.update({f"P_{c}": x[:, 0].mean(), f"R_{c}": x[:, 1].mean(), f"F1_{c}": x[:, 2].mean()})
                soy = wk[wk.true_class == "soybean"]
                row["soy_polygons_correct_mean"] = (soy.majority_prediction == "soybean").sum() / wk.variant.nunique()
                for p in a.atypical:
                    row[f"oof_{p}_correct_share"] = float((wk[wk.polygon_id == p].majority_prediction == "soybean").mean())
                other = soy[~soy.polygon_id.isin(a.atypical)]
                row["other_soy_correct_share"] = float((other.majority_prediction == "soybean").mean())
                rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(R / "PHENO_ABC.csv", index=False)
    for g in a.groups:
        if (g, "A") not in W:
            continue
        base = W[(g, "A")]
        base = base[base.true_class == "soybean"]
        for s in "BC":
            if (g, s) not in W:
                continue
            b = W[(g, s)]
            b = b[b.true_class == "soybean"]
            m = base.merge(b, on=["variant", "polygon_id"], suffixes=("_A", "_X"))
            m = m[~m.polygon_id.isin(a.atypical)]
            ca, cx = m.majority_prediction_A == "soybean", m.majority_prediction_X == "soybean"
            flips.append(dict(group=g, set=s, fixed_vs_A=int((~ca & cx).sum()), broken_vs_A=int((ca & ~cx).sum()),
                              cases=len(m), polygons_ever_changed=int(m[ca != cx].polygon_id.nunique())))
    fl = pd.DataFrame(flips)
    fl.to_csv(R / "PHENO_ABC_other_polygons_changes.csv", index=False)
    show = ["group", "set", "cv", "OA", "kappa", "target_macro_f1_px", "target_macro_f1_parcel", "F1_maize", "F1_soybean",
            "R_soybean", "F1_sunflower", "soy_polygons_correct_mean", "other_soy_correct_share"]
    (R / "PHENO_ABC.md").write_text("# Phenology feature experiment A/B/C (internal CV; recommendation for human review)\n\n"
                                    + out[[c for c in show if c in out]].round(3).to_markdown(index=False) + "\n\n## Other soybean polygons vs A\n\n"
                                    + (fl.to_markdown(index=False) if len(fl) else "") + "\n")
    print(out[[c for c in show if c in out]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
