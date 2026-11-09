# Protocol of the synthetic crop-presence experiment (known truth)

Purpose: check that the three crop-presence methods of `geocrop crop-presence` (P1 pixel majority, P2 area-weighted soft
vote, P3 segment evidence) behave as designed when the truth is known. **No real data are used and the numbers say
nothing about real accuracy.**

| Element | Specification (`synthetic/make_synthetic_declarations.py`) |
|---|---|
| Landscape | 8 x 10 cells of 25 x 25 pixels (10 m, EPSG:32633); one parcel of 22 x 22 pixels (4.84 ha) inside every cell; 80 parcels |
| Classes | forest, grass, maize, soybean, sunflower (declared crops: maize, soybean, sunflower, drawn uniformly) |
| Parcel content | background forest or grass split by a vertical line at a random column; the actual crop fills one connected rectangle covering 20-100 % of the parcel (uniform), placed at a random position |
| Wrong declarations | each parcel is wrong with probability 0.25 (drawn independently, so the number varies by seed: 19 of 80 for seed 11); a wrong parcel holds another crop or no crop at all (1 in 3 each of the two other crops or none) |
| Declared area | correct parcels: true crop area x U(0.9, 1.1), with probability 0.15 inflated by 1.8; wrong parcels: U(0.3, 0.9) of the parcel area |
| Simulated classifier | each pixel gets the true class with probability 0.85 and otherwise a uniformly drawn different class; errors are independent per pixel (no spatial correlation, so wrong pixels are isolated); probabilities are a Dirichlet(0.6) draw scaled by 0.4 plus a peak of 0.45-0.6 on the predicted class, normalised to sum 1 |
| Thresholds | the defaults of `geocrop crop-presence` as written in the code before the experiment was run and not tuned afterwards: support probability 0.5, minimum segment 0.03 ha, minimum connected support 0.05 ha, minimum supported share 0.5, low score 0.1, minimum confidence 0.6, area tolerance 0.5, minimum agricultural area 0.03 ha, minimum valid pixels 4 |
| Truth | a declaration is *correct* when the declared crop is truly present on the parcel (any area > 0); `heterogeneous` = the crop covers < 50 % of the parcel |
| Randomness | `numpy.random.default_rng(seed)`; seed 11 for the main table, seeds 1-20 for the spread; one simulation per seed |

## Software versions
Base experiments: engine commit c612404 and later commits, all contained in v1.0.0rc2; clean re-execution of E0-E8: commit 1f4509036b (on the main branch after v1.0.0rc2); crop-presence demonstration: engine commit 5f73f60fe6a413710b2339fb55b888328dd631d2 (pinned in `requirements-crop-presence.txt`). This package: the commit shown on GitHub for the version you cite.

## Run
```
scripts/run_crop_presence_demo.sh out                  # seed 11; prints and writes out/crop_presence_synthetic_scores.csv
python scripts/summarise_seeds.py --seeds 20 --out out/seeds   # 20 independent landscapes
```
Outputs in `results_aggregate/crop_presence_synthetic/`: `seed11_scores.csv`, `summary_20_seeds.csv`, `all_seeds.csv`.

## Result for seed 11 (absolute counts; 61 correct and 19 wrong declarations)
| method | correct declarations supported | wrong declarations supported |
|---|---|---|
| P1 majority, whole parcel | 33/61 (3/31 where the crop covers < 50 %) | 0/19 |
| P1 majority, agricultural part | 61/61 | 3/19 |
| P2 soft vote, agricultural part >= 0.5 | 56/61 (26/31 heterogeneous) | 0/19 |
| P3 status `supported` | 56/61 (30/31 heterogeneous) | 0/19 |

"0/19" means no wrong declaration was supported **in this simulation**, not that the error rate is negligible in general:
over 20 landscapes P1 on the agricultural part supported up to 22.7 % of the wrong declarations, while P2 and P3
supported none, and the recall of correct declarations ranged from 0.54-0.78 (P1 whole), 0.91-0.98 (P2) and 0.86-0.97
(P3). Independent per-pixel errors make isolated false pixels frequent, which favours methods that require a connected
supported area; spatially correlated classification errors, which occur in real maps, are not simulated.
