# GeoCrop reproducibility package

Companion to the paper *GeoCrop Engine: An Open and Reproducible Framework for Sentinel-Based Crop Classification,
Parcel Delineation and Declaration Verification* (under review; Lijevče polje, 2023). It lets you re-run the
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
| `configs/study_2023_resolved.yaml` | resolved configuration of the 2023 pixel-level run (from its run manifest; reference paths replaced by placeholders) |
| `aoi/` | experiment AOI (357.6 km²) and operational lowland AOI (719.4 km²) as GeoJSON, with hashes in `HASHES.md` |
| `scripts/declared_overlay.py` | aggregate overlay of a declared-parcel layer with a classification map (the comparison of Section 6.4 of the paper) |
| `results_aggregate/declared/` | aggregated outputs of that comparison (no geometries) |
| `results_aggregate/run_provenance_study.csv` | engine commit, working-tree flag, timestamp, config fingerprint and training-set hash of each run |

## What this package does not do
Without the restricted reference data the package does **not** let you re-obtain the accuracy reported in the paper; it
reproduces the workflow on synthetic data and documents the study (configuration, AOI, scene inventory, provenance,
aggregated results). The runs of the study were made with several engine commits (all contained in v1.0.0rc2); the run
manifests record that the working tree was not clean when they ran, see `results_aggregate/run_provenance_study.csv`.

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
