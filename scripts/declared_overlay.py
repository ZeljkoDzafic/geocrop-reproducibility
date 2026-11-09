"""Usage: python scripts/declared_overlay.py --declared <layer.shp|gpkg> --classes <classes.tif> --legend <class_legend.json> --out <dir> [--compare E0=<classes.tif>]

Aggregate overlay of the declared-parcel geometry (soybean, sunflower, maize 2023; one dissolved layer, no crop
attribute) with the E8 and E0 classification maps. Writes aggregates only (no geometries); declarations are
administrative claims, not ground truth, and the layer carries no per-parcel crop, so this is a consistency check."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd, rasterio
from rasterio import features

import argparse
ap = argparse.ArgumentParser()
ap.add_argument("--declared", required=True, help="declared-parcel layer (one dissolved layer is enough; no attributes are used)")
ap.add_argument("--classes", required=True, help="classification raster of the main map (labelled E8 in the outputs)")
ap.add_argument("--legend", required=True, help="class_legend.json written by `geocrop predict`")
ap.add_argument("--compare", help="second classification raster (labelled E0)")
ap.add_argument("--out", required=True)
args = ap.parse_args()
SHP = Path(args.declared)
OUT = Path(args.out); OUT.mkdir(parents=True, exist_ok=True)
LEG = {int(k): v for k, v in json.load(open(args.legend)).items()}
TARGET = {"maize", "soybean", "sunflower"}
g = gpd.read_file(SHP)
with rasterio.open(args.classes) as ref:
    crs, tr, shape = ref.crs, ref.transform, (ref.height, ref.width)
m = g.to_crs(crs)
parts = list(m.geometry.iloc[0].geoms)
area_ha = np.array([p.area for p in parts]) / 1e4
res = {"layer_features": int(len(g)), "dissolved_parts": len(parts), "total_ha": float(area_ha.sum()),
       "part_ha_percentiles_5_25_50_75_95": [float(x) for x in np.percentile(area_ha, [5, 25, 50, 75, 95])],
       "parts_with_holes": int(sum(len(p.interiors) for p in parts))}
bins = [0, 0.1, 0.2, 0.5, 1, 2, 5, 1e9]; labels = ["<0.1", "0.1-0.2", "0.2-0.5", "0.5-1", "1-2", "2-5", ">=5"]
cut = pd.cut(area_ha, bins, labels=labels, right=False)
size = pd.DataFrame({"size_class_ha": labels, "parts": [int((cut == l).sum()) for l in labels],
                     "area_ha": [float(area_ha[cut == l].sum()) for l in labels]})
size["share_of_area"] = size.area_ha / size.area_ha.sum()
size.to_csv(OUT / "declared_parts_size_classes.csv", index=False)
ids = features.rasterize(((p, i + 1) for i, p in enumerate(parts)), out_shape=shape, transform=tr, fill=0, dtype="int32")
inside = ids > 0
rows, partrows = [], []
for name, path in [("E8", Path(args.classes))] + ([("E0", Path(args.compare))] if args.compare else []):
    with rasterio.open(path) as r:
        c = r.read(1)
    nod = c == 255 if c.dtype == np.uint8 else c < 0
    valid = ~nod
    tot = {LEG[k]: int(((c == k) & valid).sum()) for k in LEG}
    inn = {LEG[k]: int(((c == k) & valid & inside).sum()) for k in LEG}
    ntarget_map = sum(tot[k] for k in TARGET)
    ntarget_in = sum(inn[k] for k in TARGET)
    row = {"map": name, "declared_pixels": int((inside & valid).sum()),
           "declared_ha_from_pixels": (inside & valid).sum() / 100,
           "share_declared_pixels_mapped_target": ntarget_in / max((inside & valid).sum(), 1),
           "target_ha_map_total": ntarget_map / 100, "target_ha_map_inside_declared": ntarget_in / 100,
           "share_of_mapped_target_inside_declared": ntarget_in / max(ntarget_map, 1)}
    for k in sorted(TARGET):
        row[f"mapped_{k}_ha_total"] = tot[k] / 100
        row[f"mapped_{k}_ha_inside_declared"] = inn[k] / 100
    for k in LEG.values():
        row[f"share_declared_pixels_{k}"] = inn[k] / max((inside & valid).sum(), 1)
    rows.append(row)
    # per dissolved part: majority class of pixels whose centre lies inside the part
    cc = np.where(valid, c, 255)
    flat_ids, flat_c = ids[inside], cc[inside]
    n = len(parts) + 1
    cnt = np.zeros((n, 10), dtype=np.int64)
    np.add.at(cnt, (flat_ids, np.where(flat_c == 255, 9, flat_c)), 1)
    cnt = cnt[1:, :9]
    npx = cnt.sum(axis=1)
    maj = cnt.argmax(axis=1)
    for i in range(len(parts)):
        partrows.append({"map": name, "part": i, "ha": area_ha[i], "pixels": int(npx[i]),
                         "majority": LEG[int(maj[i])] if npx[i] else None,
                         "target_share": float(sum(cnt[i, k] for k in LEG if LEG[k] in TARGET) / npx[i]) if npx[i] else np.nan})
pd.DataFrame(rows).T.to_csv(OUT / "declared_overlay_maps.csv", header=False)
pr = pd.DataFrame(partrows)
pr = pr[pr.pixels > 0]
pr["size_class_ha"] = pd.cut(pr.ha, bins, labels=labels, right=False)
pr["majority_is_target"] = pr.majority.isin(TARGET)
summ = pr.groupby(["map", "size_class_ha"], observed=True).agg(parts=("part", "count"), majority_target=("majority_is_target", "mean"),
                                                                 mean_target_share=("target_share", "mean")).reset_index()
summ.to_csv(OUT / "declared_parts_agreement_by_size.csv", index=False)
allm = pr.groupby("map").agg(parts_with_pixels=("part", "count"), majority_target=("majority_is_target", "mean"),
                              mean_target_share=("target_share", "mean")).reset_index()
allm.to_csv(OUT / "declared_parts_agreement.csv", index=False)
json.dump(res, open(OUT / "declared_layer_summary.json", "w"), indent=1)
print(json.dumps(res, indent=1)); print(size.round(3).to_string(index=False)); print(pd.DataFrame(rows).T.round(3).to_string()); print(allm.round(3).to_string(index=False)); print(summ.round(3).to_string(index=False))
