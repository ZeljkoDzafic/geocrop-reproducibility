"""Score the three crop-presence methods against the KNOWN truth of the synthetic declarations.

    python scripts/compare_crop_presence.py --presence out/crop_presence/crop_presence.csv --truth out/declarations/truth.csv

A parcel's declaration is *correct* when the declared crop is truly present (truth_present). For each method the
parcel is 'supported' when: A_whole / A_agricultural = the pixel majority equals the declared crop; B = soft vote on
the agricultural part >= 0.5; C = preliminary_status == supported (status 'disputed_review' counts as not supported
here, so the table shows the price of review). Synthetic truth only: it checks the code, not real accuracy.
"""
import argparse

import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--presence", required=True)
    ap.add_argument("--truth", required=True)
    ap.add_argument("--min-presence-share", type=float, default=0.0, help="truth: minimum crop share of the parcel")
    a = ap.parse_args()
    p, t = pd.read_csv(a.presence), pd.read_csv(a.truth)
    d = p.merge(t, on="parcel_id")
    d["truth"] = d.truth_present & (d.crop_share_of_parcel > a.min_presence_share)
    d["het"] = d.crop_share_of_parcel < 0.5
    methods = {"A_pixel_majority_whole": d.a_match_whole.fillna(False).astype(bool),
               "A_pixel_majority_agricultural": d.a_match_agricultural.fillna(False).astype(bool),
               "B_soft_vote_agricultural>=0.5": (d.soft_vote_agricultural.fillna(0) >= 0.5),
               "C_evidence_status_supported": d.preliminary_status.eq("supported")}
    rows = []
    for name, flag in methods.items():
        for subset, mask in (("all", d.index == d.index), ("heterogeneous (crop < 50 % of parcel)", d.het)):
            m = mask & d.truth
            n = mask & ~d.truth
            rows.append({"method": name, "subset": subset, "parcels": int(mask.sum()),
                         "correct_declarations": int(m.sum()), "recall_of_correct": float(flag[m].mean()) if m.sum() else None,
                         "wrong_declarations": int(n.sum()), "wrongly_supported": float(flag[n].mean()) if n.sum() else None})
    out = pd.DataFrame(rows)
    status = d.groupby(["preliminary_status", "truth"]).size().unstack(fill_value=0)
    area = d[d.truth].copy()
    area["err_pct"] = 100 * (area.crop_area_ha - area.true_crop_area_ha) / area.true_crop_area_ha
    print(out.round(3).to_string(index=False))
    print("\nPreliminary status vs truth (rows: status; columns: declared crop truly present?)\n", status.to_string())
    print("\nMapped crop area vs true crop area on parcels with the crop present: median error %.1f %%, IQR %.1f to %.1f %%"
          % (area.err_pct.median(), area.err_pct.quantile(.25), area.err_pct.quantile(.75)))
    out.to_csv("crop_presence_synthetic_scores.csv", index=False)


if __name__ == "__main__":
    main()
