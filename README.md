# GeoCrop reproducibility package

Companion to the paper *GeoCrop Engine: An Open and Reproducible Framework for Sentinel-Based Crop Classification and Parcel-Level Review Support* (under review; Lijevče polje, 2023). It lets you re-run the
**sensitivity workflow** of the paper on synthetic data, and gives the aggregated study results and the scene inventory.

> Results here are internal cross-validation outputs, a recommendation for human review and not a definitive
> conclusion. The synthetic demo reproduces the *workflow*, not the study's numbers. The real reference polygons and
> declarations are not distributed ([DATA_POLICY.md](DATA_POLICY.md)).

Project website: https://geocropengine.rs.ba/ · Engine: https://github.com/ZeljkoDzafic/geocrop-engine

## Contents
| Path | What |
|---|---|
| `synthetic/make_synthetic_dataset.py` | synthetic samples (9 classes, seasonal curves, three atypical soybean polygons) |
| `scripts/run_sensitivity_demo.sh` | phenology features, A/B/C sets, partition-sensitivity CV, comparison table |
| `scripts/compare_pheno.py` | one table for the A/B/C experiment from `geocrop cv-stability` outputs |
| `results_aggregate/` | aggregated study results (overall metrics, partition spread, all-variants summary) |
| `scenes/scenes_2023_imported.csv` | 82 Sentinel-2 and 44 Sentinel-1 scenes imported for the study (public data) |
| `configs/study_clean.yaml`, `configs/study_s1coreg.yaml` | configurations of the clean re-execution (uncorrected Sentinel-1) and of the co-registration sensitivity run, reference paths replaced by placeholders |
| `results_aggregate/coreg/` | aggregated Sentinel-1 co-registration results: offsets by geometry, before/after E0-E8, paired results over 12 partitions, map agreement and class-area changes (no geometries, no polygon ids) |
| `configs/study_2023_resolved.yaml` | resolved configuration of the 2023 pixel-level run (from its run manifest; reference paths replaced by placeholders) |
| `aoi/` | experiment AOI (357.6 km²) and operational lowland AOI (719.4 km²) as GeoJSON, with hashes in `HASHES.md` |
| `synthetic/make_synthetic_declarations.py`, `scripts/run_crop_presence_demo.sh`, `scripts/compare_crop_presence.py` | synthetic declared parcels with known truth, the `crop-presence` run and its scoring |
| `results_aggregate/declarations/` | aggregated results of `geocrop crop-presence` on the 4,998 declarations of 2023 (no identifiers, cadastral keys or geometries; Section 6.4 and Supplementary S11 of the paper) |
| `results_aggregate/run_provenance_study.csv` | engine commit, working-tree flag, timestamp, config fingerprint and training-set hash of each run |

## Declared crop in heterogeneous parcels (`crop-presence`), synthetic with known truth
`scripts/run_crop_presence_demo.sh` generates 80 synthetic cadastral-like parcels (forest, grass and a connected crop block;
about a quarter of the declarations wrong by construction), simulates a classifier that is right for ~85 % of pixels,
runs `geocrop crop-presence` and scores three methods against the known truth: **P1** pixel majority (whole parcel and
agricultural part), **P2** area-weighted soft vote, **P3** segment-based evidence with the largest connected supported area.
It shows that the code separates a heterogeneous parcel from a wrong declaration and what the review status costs. It
does **not** show real accuracy, the thresholds of the preliminary status are not validated, and without field-verified
parcels none of the methods can be scored on real data. Approval of a declaration is an administrative decision, not a
field verification. The command is part of GeoCrop Engine release candidate v1.0.0rc3 (engine commit e59f0b76, added after v1.0.0rc2; Zenodo DOI 10.5281/zenodo.24104638, all versions 10.5281/zenodo.24078244), pinned in `requirements-crop-presence.txt`.

```
pip install -r requirements-crop-presence.txt
scripts/run_crop_presence_demo.sh out
```

## Sentinel-1 co-registration (sensitivity analysis, aggregated results)

`results_aggregate/coreg/` holds the aggregated results of the check of the Sentinel-1 / Sentinel-2 alignment (no geometries, no polygon identifiers):
`coreg_offsets_by_geometry.csv` (estimate on windows P1-P2, independent verification on P3-P4, per acquisition geometry),
`coreg_composite_level_by_direction.csv` (residuals of the composites, pooled and independent windows),
`coreg_before_after_E0_E8.csv` (main five-fold 5 km partition), `coreg_paired_by_partition.csv` and `coreg_paired_summary.csv`
(E3, E4, E8 over 12 spatial partitions), `coreg_map_class_areas.csv` and `coreg_map_agreement.json` (E8 maps from uncorrected and corrected data).

**Which results belong to which experiment.** The numbers of the paper and of `clean_reexecution_E0_E8.csv` are the *original,
uncorrected* experiment (raw Sentinel-1 scenes). Everything in `coreg/` that says *corrected* is a *later sensitivity analysis* with
Sentinel-1 scenes shifted by the estimated per-geometry offsets (uncorrected: `study_clean.yaml`, corrected: `study_s1coreg.yaml`; they differ only in
the Sentinel-1 scene, composite and feature paths). Both were run from the clean engine commit `1f4509036bbf51ad7dd8019e72526760add65992` (Python 3.12,
scikit-learn 1.9.1). Offsets are *estimated relative shifts between the sensors* (correlation of VH backscatter with NDVI, r about 0.4-0.55, 2-6 scenes per
estimate), not absolute geolocation errors; sign convention: reference[y, x] ~ Sentinel-1[y + dy, x + dx], positive dy south, positive dx east, pixel 10 m;
the correction shifts linear power by (-dy, -dx) with bilinear interpolation and skips offsets below 0.5 px. The restricted run directories and the
scripts that produced the tables are not part of the public package; the commands in the paper's supplement and the engine's co-registration function
(`geocrop.s1_stac.estimate_offsets`, `geocrop.acceptance.coregistration`) reproduce the procedure on your own data. The automatic correction is an option
with quality control and should not be applied unconditionally to a new data set.

## Crop presence on the real declarations (aggregated results only)
`results_aggregate/declarations/` holds the aggregated outputs behind Section 6.4 and Supplementary Section S11: methods by declared crop, by parcel size and by agricultural share, method agreement, E0 versus E8, OBIA versus pseudo-segments, threshold sensitivity and the data checks. The declaration layer (4,998 declarations with cadastral keys) is protected and is not distributed, so these tables cannot be re-created from this package; they are consistency numbers, not accuracy (there is no field verification of the declared crops).
How they were produced: engine commit `a647946` (branch `release/1.0.0rc3`, containing `crop-presence` from commit `5f73f60`), `geocrop crop-presence --probabilities <E8 or E0 probabilities> --parcels <neutral parcel file> --declared-area-field declared_area_ha --out <dir>` with the default, unvalidated thresholds (support probability 0.5, minimum segment 0.03 ha, minimum connected support 0.05 ha, minimum supported share 0.5, low score 0.1, minimum confidence 0.6, area tolerance 0.5, minimum agricultural area 0.03 ha; agricultural part: maize, soybean, sunflower, vegetables, winter crops); OBIA segments from `geocrop segment-obia --bands P3_B04 P3_B08 P3_B11 P3_NDVI --segments-per-km2 100 --compactness 10` with the AOI mask (35,449 segments, parameters not tuned).

## What this package does not do
Without the restricted reference data the package does **not** let you re-obtain the accuracy reported in the paper; it
reproduces the workflow on synthetic data and documents the study (configuration, AOI, scene inventory, provenance,
aggregated results). The runs of the study were made with several engine commits (all contained in v1.0.0rc2); the run
manifests record that the working tree was not clean when they ran, see `results_aggregate/run_provenance_study.csv`.

Protocol, parameters, absolute counts and the spread over 20 seeds of the synthetic crop-presence experiment: [PROTOCOL_crop_presence_synthetic.md](PROTOCOL_crop_presence_synthetic.md). The clean re-execution of the main experiments (identical results from commit `1f4509036b`) is in `results_aggregate/clean_reexecution_E0_E8.csv`; the configuration of the main run is `configs/study_2023_main_run_resolved.yaml`.

## Run the demo
```
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt            # GeoCrop Engine v1.0.0rc2 + tabulate
scripts/run_sensitivity_demo.sh out        # ~10 minutes on a laptop; writes out/pheno/PHENO_ABC.md
```
The demo uses the engine commands `geocrop phenology-features` and `geocrop cv-stability --feature-sets/--feature-set`
(documented in the engine's `docs/sensitivity.md`): the same samples, the same spatial partitions and the same Random
Forest settings for every feature set, post-season and with the season cut on day 196 and 226.

## Use it on your own data
Provide a `samples.npz` from `geocrop samples` (with `ts_<index>_d<doy>` columns) and window names with end days, then
follow `scripts/run_sensitivity_demo.sh`.

## How to cite
Use `CITATION.cff` (archived with a Zenodo DOI once released) and cite the engine release as well:
GeoCrop Engine v1.0.0rc2, https://doi.org/10.5281/zenodo.24078771.

## Licence
Code and synthetic data: Apache-2.0 (see `LICENSE`). Aggregated result tables: CC-BY-4.0.
