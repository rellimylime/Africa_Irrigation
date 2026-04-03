# 2_water_source_analysis

Notebooks that investigate where the water actually comes from for center pivot irrigation systems (CPIS) in arid Sub-Saharan Africa. The analyses build on the expansion findings in `1_analyze_data/` and address the core open question: if dams alone can't explain CPIS growth (3% dam growth vs 191% CPIS growth), what can?

Run in order: 1 → 2 → 3 → 4 → 5. Notebooks 2 and 3 are independent of each other and of notebook 1.

---

## Narrative arc

| Step | Notebook | Question answered |
|------|----------|-------------------|
| 1 | `1_ndwi_analysis.ipynb` | Which CPIS are actively irrigating? (Cleans the denominator) |
| 2 | `2_dem_flow_analysis.ipynb` | Which CPIS could physically receive gravity-fed dam water? (Core finding) |
| 3 | `3_groundwater_gp_regression.ipynb` | Where is groundwater productivity high enough to supply the rest? |
| 4 | `4_anomaly_detection.ipynb` | Which CPIS are unexplained by either source? (Flags priorities) |
| 5 | `5_spatial_statistics.ipynb` | Do CPIS cluster near dams beyond chance? What spatial patterns explain dam proximity? |

---

## 1_ndwi_analysis.ipynb

**What it does:** Computes NDWI = (Green − NIR) / (Green + NIR) from Sentinel-2 bands B03 and B8A over each CPIS polygon and classifies systems as actively irrigated (mean NDWI > 0) or inactive.

**Why it's necessary:** Chen et al. (2023) mapped every CPIS-shaped object, including fallow and abandoned systems. Analyzing water sourcing for inactive systems inflates the denominator and dilutes the signal. This notebook produces the cleaned active-CPIS subset used in notebooks 2–4.

**Data requirement:** Sentinel-2 Level-2A imagery must be downloaded separately. A complete GEE export script is provided inside the notebook.

**Outputs:**
- `NDWI_output_tif_path` — continuous NDWI raster over the study domain
- `Active_CPIS_shp_path` — CPIS polygons with mean NDWI > 0 (actively irrigating)
- `Inactive_CPIS_shp_path` — CPIS polygons with mean NDWI ≤ 0 (fallow or abandoned)
- `CPIS_NDWI_stats_csv_path` — per-polygon mean, min, max, std NDWI

---

## 2_dem_flow_analysis.ipynb

**What it does:** Samples SRTM elevation at each CPIS centroid and its nearest dam, then classifies each CPIS as: **feasible** (within 50 km and downhill from its nearest dam), **infeasible by elevation** (within 50 km but uphill), or **infeasible by distance** (nearest dam > 50 km). Also computes D8 flow direction using RichDEM.

**Why it's necessary:** Notebook `3_Dams_AEI_Targeting_Ratios.ipynb` found weak spatial concentration of CPIS near dams. This notebook explains why: radial distance ignores topography. A CPIS 10 km from a dam but 200 m uphill cannot receive gravity-fed surface water. Adding elevation constraints produces the "serviceable dam" definition behind the project's core finding that most CPIS are beyond serviceable dam range.

**Outputs:**
- `CPIS_Elevation_Classified_shp_path` — CPIS labeled feasible / infeasible_elevation / infeasible_distance / unknown; used as primary input to notebook 4
- `Dam_CPIS_Profiles_csv_path` — pairwise table of dam–CPIS distance, elevation difference, and classification for each CPIS

**Figures:** Three-color map of CPIS by accessibility class across arid SSA; threshold sensitivity table comparing feasibility fractions at 25, 50, and 100 km cutoffs.

---

## 3_groundwater_gp_regression.ipynb

**What it does:** Fits a Gaussian Process regression (ConstantKernel × RBF + WhiteKernel) to the MacDonald et al. (2012) categorical groundwater productivity map, produces a continuous prediction surface and 1σ uncertainty raster at 0.25° resolution, and predicts GP groundwater productivity at each CPIS centroid.

**Why it's necessary:** CPIS that are elevation-infeasible for dam water must be using groundwater or an undocumented source. The MacDonald et al. map is categorical and coarse. GP regression converts it into a continuous, spatially smooth surface with quantified uncertainty — enabling the feature-based anomaly detection in notebook 4 and revealing spatial gradients hidden in the discrete original classes.

**Computational note:** GP fitting is O(n³); this notebook subsamples to 2,000 training points by default. Increase `MAX_TRAIN_POINTS` with more RAM.

**Outputs:**
- `GP_Groundwater_Prediction_tif_path` — continuous GP-predicted productivity raster (0.25° resolution over arid SSA)
- `GP_Groundwater_Uncertainty_tif_path` — GP 1σ uncertainty raster (high values = sparse training data, low confidence)
- `CPIS_GP_Groundwater_csv_path` — GP prediction and uncertainty at each CPIS centroid; primary groundwater feature for notebook 4

**Figures:** Three-panel plot: original categorical groundwater map, GP mean prediction surface, GP uncertainty surface.

---

## 4_anomaly_detection.ipynb

**What it does:** Builds a six-feature matrix for each CPIS (distance to nearest dam, elevation difference to nearest dam, aridity index, GP groundwater productivity, elevation, log CPIS area) and fits an Isolation Forest (contamination = 5%) to identify CPIS that are simultaneously outliers across all water source dimensions.

**Why it's necessary:** After notebooks 2 and 3 classify CPIS by dam accessibility and groundwater availability, some systems remain unexplained — too far from serviceable dams and in low-groundwater zones. These anomalies are the scientifically most important: they may have undocumented water sources, may be over-extracting, or may reveal gaps in the underlying datasets. The Isolation Forest identifies the 5% most anomalous systems without requiring hard thresholds on any single feature.

**Fallback behavior:** If notebook 2's elevation CSV is missing, notebook 4 recomputes dam distances from scratch. If notebook 3's GP CSV is missing, it falls back to the categorical MacDonald groundwater classes.

**Outputs:**
- `CPIS_Feature_Matrix_csv_path` — six-feature matrix for every CPIS (used for reproducibility and follow-on analysis)
- `CPIS_Anomaly_Scores_csv_path` — raw Isolation Forest anomaly score and binary anomaly flag per CPIS
- `CPIS_Anomalies_shp_path` — shapefile of flagged anomalous CPIS for GIS mapping and fieldwork prioritization

**Figures:** Map of anomalous vs normal CPIS across arid SSA; feature distribution comparisons (violin/box plots) between anomalous and normal groups.

---

## 5_spatial_statistics.ipynb

**What it does:** Three complementary spatial analyses that address the limitations of the targeting ratio by incorporating spatial clustering, local heterogeneity, and flow-path connectivity:

1. **Bivariate Cross-K function** — K_AB(t) = (area / (n_A × n_B)) × Σ I(d(A_i,B_j) ≤ t); L-transformed; 99% Monte Carlo CSR envelope from random redistribution of dam locations. Tests whether CPIS cluster near dams beyond what random chance predicts at each distance band.
2. **Geographically Weighted Regression (GWR)** — `mgwr` adaptive-bandwidth GWR; response = log(dist to nearest dam + 1); predictors = GP groundwater productivity, aridity index, elevation. Produces local R² and local coefficient surfaces showing *where* and *how strongly* each factor explains dam proximity.
3. **D8 flow path connectivity** — traces D8 flow direction downstream from each elevation-feasible CPIS; flags which CPIS are hydrologically connected to a dam within 500 steps (~45 km). Converts the binary feasible/infeasible elevation classification into a stricter flow-path test.

**Why it's necessary:** The targeting ratio shows *whether* CPIS are near dams but cannot distinguish spatial clustering from chance, cannot capture heterogeneity across arid zones, and uses Euclidean distance rather than the flow paths that water actually follows. These three analyses address each limitation in turn.

**Fallback behavior:** GWR section skips gracefully if `CPIS_Elevation_Classified_shp_path` (notebook 2) or `GP_Groundwater_Prediction_tif_path` (notebook 3) are missing. Flow tracing skips if the elevation-classified shapefile is absent.

**Outputs:**
- `CPIS_GWR_Results_csv_path` — per-CPIS local R², local intercept, and local coefficients for each GWR predictor
- `CPIS_Flow_Connectivity_shp_path` — elevation-feasible CPIS labeled `flow_connected` (True/False) with flow path length in metres

**Figures:**
- `5_Figure0.png` — bivariate cross-K L(t) curve with 99% CSR envelope
- `5_Figure2.png` — GWR local R² map and coefficient maps for each predictor
- `5_Figure3.png` — map of flow-connected vs disconnected feasible CPIS across arid SSA
