# Africa_Irrigation

Project assessing how much of irrigation expansion in Africa, and in Sub-Saharan Africa (SSA), is attributable to center pivot irrigation systems (CPIS) from 2000 to 2021, and investigating the water sources that supply those systems.

## Research Context

Chen et al. (2023) produced the first global inventory of CPIS in arid regions using instance segmentation on Sentinel-2 imagery. Their work answers **where CPIS are**. This project answers **where their water comes from**.

The core finding, presented at AGU Fall Meeting 2024 and the Mantell Symposium: CPIS are expanding rapidly in SSA — a 191% increase from 2000 to 2021 — but most systems operate beyond serviceable dam range (> 50 km or uphill). "Serviceable" here means elevation-feasible, not just geographically close: a CPIS 10 km from a dam but 200 m uphill cannot use gravity-fed surface water. This distinction raises urgent questions about groundwater sustainability and agricultural water policy across the region.

## Repository structure

```txt
Africa_Irrigation/
│
├── Code/
│   ├── 0_process_data/             (download, filter, preprocess datasets)
│   ├── 1_analyze_data/             (CPIS expansion and irrigation trend analyses)
│   └── 2_water_source_analysis/    (NDWI, DEM flow, groundwater GP, anomaly detection)
│
├── Data/
│   ├── Raw/               (external inputs, unmodified)
│   └── Processed/         (intermediate and final processed artifacts)
│
├── Output/
│   ├── Process/           (figures and tables from preprocessing)
│   └── Analyze/           (figures and tables from analyses)
│
├── config.yaml            (all dataset locations and brief descriptions)
└── README.md              (this file)
```

Each folder has its own README with inputs, outputs, and run notes. The exact locations of datasets used in any notebook are specified in config.yaml.

## Setup

1. Install Conda

2. Create the environment and install requirements:

```bash
conda env create -n irrigation -f requirements.yml
conda activate irrigation
```

## Quick start

1. Set paths in config.yaml to your local copies of the required datasets.

2. Run the preprocessing notebooks in Code/0_process_data as needed.

3. Run the analysis notebooks in Code/1_analyze_data or Code/2_water_source_analysis.

4. See outputs under Output/Process and Output/Analyze.

Detailed, step-by-step instructions are in the sub-READMEs inside each code folder.

## Methods

- **Geospatial expansion analysis** — CPIS area and count tracked from 2000 to 2021 against total area equipped for irrigation (AEI), disaggregated by country, region, and aridity class.
- **NDWI remote sensing** — Sentinel-2 Normalized Difference Water Index used to classify CPIS as actively irrigated vs fallow or abandoned, providing a cleaned denominator for water source analysis.
- **DEM-based flow modeling** — SRTM elevation data and RichDEM flow direction used to assess whether each CPIS is topographically downslope from its nearest dam, distinguishing elevation-feasible from infeasible surface water access.
- **Gaussian process regression** — MacDonald et al. (2012) categorical groundwater productivity interpolated into a continuous, uncertainty-quantified surface using sklearn GaussianProcessRegressor.
- **Isolation Forest anomaly detection** — Multi-feature outlier detection flags CPIS that are simultaneously far from serviceable dams and in low-groundwater areas, identifying systems whose water sources remain unexplained.
- **Bivariate Cross-K function** — Tests spatial clustering of CPIS relative to dams at increasing distance bands against a Monte Carlo CSR null, capturing co-location signal the targeting ratio cannot.
- **Geographically Weighted Regression (GWR)** — Local regression with adaptive bandwidth reveals spatial non-stationarity in what drives dam proximity, producing coefficient maps rather than a single global estimate.
- **D8 flow path connectivity** — Hydrological tracing from elevation-feasible CPIS downstream to dams, replacing Euclidean distance with actual flow-path distance.

## Key analyses and results

### A. Irrigation vs CPIS expansion (2000 to 2021)
Notebook: [Code/1_analyze_data/0_CPIS_vs_Total.ipynb](Code/1_analyze_data/0_CPIS_vs_Total.ipynb)

Representative figures:

- [Output/Analyze/0_Figure1.png](Output/Analyze/0_Figure1.png) (Africa)
- [Output/Analyze/0_Figure2.png](Output/Analyze/0_Figure2.png) (SSA)
- [Output/Analyze/0_Figure3.png](Output/Analyze/0_Figure3.png) (combined axes)

Results at a glance:

- Africa: area equipped for irrigation increased by about 51.6%. CPIS area increased by about 148.9%.
- SSA: area equipped for irrigation increased by about 94.6%. CPIS area increased by about 191.2%.
- CPIS share of irrigated area increased (Africa: ~3.6% → ~6.0%, SSA: ~6.8% → ~10.2%).

### B. Country and regional distribution
Notebook: [Code/1_analyze_data/1_CPIS_Africa_Map.ipynb](Code/1_analyze_data/1_CPIS_Africa_Map.ipynb)

Related notebook: [Code/1_analyze_data/2_CPIS_by_Region.ipynb](Code/1_analyze_data/2_CPIS_by_Region.ipynb)

Representative figure: [Output/Analyze/1_Figure1.png](Output/Analyze/1_Figure1.png)

What it shows:

- Country-level maps for 2000 and 2021, CPIS percent of total area equipped for irrigation.
- Views masked to SSA and aridity zones to highlight spatial patterns.

### C. Dam growth context
Notebook: [Code/1_analyze_data/4_Dam_Growth_Context.ipynb](Code/1_analyze_data/4_Dam_Growth_Context.ipynb)

What it shows:

- Dam count in arid SSA grew from 2,674 (2000) to 2,763 (2021) — roughly 3% growth.
- Contrasted against 191% CPIS expansion over the same period, this establishes that dam infrastructure alone cannot explain CPIS growth.
- Country-level maps of new dams constructed 2000–2021.

### D. CPIS–dam spatial association
Notebook: [Code/2_water_source_analysis/5_spatial_statistics.ipynb](Code/2_water_source_analysis/5_spatial_statistics.ipynb)

What it tests:

- Whether CPIS cluster near dams beyond chance (bivariate cross-K vs CSR envelope).
- Where and how strongly groundwater, aridity, and elevation predict dam-distant siting (GWR local coefficients).
- Which elevation-feasible CPIS are actually hydrologically connected to a dam via D8 flow paths.

Headline takeaway: A motivating CDF in the notebook shows the raw distance distribution; the cross-K, GWR, and flow-path analyses then unpack the spatial structure the simple distance metric cannot reveal.

### E. NDWI-based activity classification
Notebook: [Code/2_water_source_analysis/1_ndwi_analysis.ipynb](Code/2_water_source_analysis/1_ndwi_analysis.ipynb)

What it does:

- Computes NDWI = (Green − NIR) / (Green + NIR) from Sentinel-2 imagery.
- Classifies each CPIS polygon as actively irrigated (mean NDWI > 0) or inactive.
- Provides the cleaned active-CPIS denominator used in the elevation and groundwater analyses.

Note: Requires Sentinel-2 imagery download (GEE export script included in notebook).

### F. DEM-based flow and elevation accessibility
Notebook: [Code/2_water_source_analysis/2_dem_flow_analysis.ipynb](Code/2_water_source_analysis/2_dem_flow_analysis.ipynb)

What it does:

- Samples SRTM elevation at CPIS centroids and dam locations.
- Classifies each CPIS as elevation-feasible (downhill from nearest dam within 50 km), infeasible by elevation (uphill), or infeasible by distance.
- Computes D8 flow direction using RichDEM.
- Compares elevation-aware vs radial-distance accessibility across distance thresholds.

Headline takeaway: A substantial fraction of CPIS that appear "nearby" a dam by radial distance are uphill from it, explaining the weak concentration patterns in the distance-based targeting ratios.

### G. Gaussian process groundwater regression
Notebook: [Code/2_water_source_analysis/3_groundwater_gp_regression.ipynb](Code/2_water_source_analysis/3_groundwater_gp_regression.ipynb)

What it does:

- Fits a Gaussian Process regression (ConstantKernel × RBF + WhiteKernel) to the MacDonald et al. (2012) categorical groundwater productivity data.
- Produces a continuous prediction surface and a 1σ uncertainty raster over arid SSA.
- Predicts GP groundwater productivity at each CPIS centroid for use in anomaly detection.

### H. Isolation Forest anomaly detection
Notebook: [Code/2_water_source_analysis/4_anomaly_detection.ipynb](Code/2_water_source_analysis/4_anomaly_detection.ipynb)

What it does:

- Builds a six-feature matrix per CPIS: distance to dam, elevation difference, aridity index, groundwater productivity, elevation, and log CPIS area.
- Fits Isolation Forest to identify the most anomalous 5% of systems.
- Maps anomalies and compares feature distributions between anomalous and normal CPIS.

Headline takeaway: Anomalous CPIS — far from dams, uphill, in low-groundwater zones — mark where future fieldwork, satellite monitoring, and water policy attention are most needed.

### I. Spatial statistics
Notebook: [Code/2_water_source_analysis/5_spatial_statistics.ipynb](Code/2_water_source_analysis/5_spatial_statistics.ipynb)

What it does:

- **Bivariate Cross-K function** — tests whether CPIS cluster near dams beyond what random chance predicts at each distance band, with a 99% Monte Carlo CSR envelope.
- **Geographically Weighted Regression (GWR)** — adaptive-bandwidth GWR predicts log(dam distance) from groundwater productivity, aridity, and elevation; outputs local R² and coefficient surfaces showing where and how strongly each factor operates.
- **D8 flow path connectivity** — traces RichDEM D8 flow paths downstream from elevation-feasible CPIS to determine whether each system is hydrologically connected to a dam, adding a flow-path test stricter than radial distance alone.

Figures: [Output/Analyze/5_Figure0.png](Output/Analyze/5_Figure0.png), [Output/Analyze/5_Figure2.png](Output/Analyze/5_Figure2.png), [Output/Analyze/5_Figure3.png](Output/Analyze/5_Figure3.png)

## Data sources (primary)

Citations and links for the main external datasets. All paths are configured in [config.yaml](config.yaml).

Preprocessing steps are documented in the [Code/0_process_data](Code/0_process_data) sub-README.

- CPIS shapefiles, 2000 and 2021, DetectCPIS project (see repository for download instructions).
- AQUASTAT dissemination system tables (Africa and SSA subsets, selected years between 2000 and 2021).
- GRanD / GDW dams database (Africa and arid SSA subsets).
- Global Aridity Index and PET v2 (aridity classes and masks).
- Area Equipped for Irrigation rasters, 2000 and 2015, including MEIER products where used.
- Groundwater productivity maps for Africa (MacDonald et al. 2012).
- Sentinel-2 Level-2A surface reflectance imagery (bands B03, B8A) — download instructions in notebook 5.
- SRTM-derived DEM for Africa — processed version at `Africa_Elevation_Reprojected_tif_path`.

Notes:

- Some countries or territories are not present in AQUASTAT for the selected extracts (see config.yaml and the process README for handling choices).
- All derived products are written to Data/Processed and Output/Process.

## Reproducibility

- Pin the environment with requirements.yml.
- Keep config.yaml as the single source of truth for data paths and dataset descriptions.
- Each notebook reads only from paths defined in config.yaml and from artifacts produced by the process notebooks.

## References

- Chen, F., Zhao, H., Roberts, D., et al. 2023. Mapping center pivot irrigation systems in global arid regions using instance segmentation and analyzing their spatial relationship with freshwater resources. Remote Sensing of Environment 297, 113760.

- MacDonald, A. M., Bonsor, H. C., Ó Dochartaigh, B. E., Taylor, R. G. 2012. Quantitative maps of groundwater resources in Africa. Environmental Research Letters 7, 024009.

- Ramankutty, N., Evan, A. T., Monfreda, C., Foley, J. A. 2010. Global Agricultural Lands: Croplands, 2000. NASA SEDAC. https://doi.org/10.7927/H4C8276G

- Additional citations and dataset DOIs are listed in the sub-READMEs and [config.yaml](config.yaml).

## Presentations

- Miller E, Boser A, Caylor K. "Satellite Data Reveal Emerging Decentralized Irrigation Systems in Sub-Saharan Africa." Summer@Bren 2024 Flash Talks. August 2024.

- Miller E, Boser A, Caylor K. "Water Source Attribution for Center Pivot Irrigation in Sub-Saharan Africa." Mantell Symposium, UCSB. October 2024.

- Boser A, Miller E, Perez J, Caylor K. "Analyzing the sustainability and climate resilience of rapidly expanding center pivot irrigation in Sub-Saharan Africa using remote sensing." AGU Fall Meeting. December 2024.
