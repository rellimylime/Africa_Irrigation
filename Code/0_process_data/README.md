# 0_process_data

Preprocessing pipeline that converts raw external datasets into the cleaned, spatially harmonized inputs required by all analysis notebooks. Run these in order before anything in `1_analyze_data/` or `2_water_source_analysis/`.

---

## 0_Filter_AQUASTAT.ipynb

**What it does:** Filters the global AQUASTAT irrigation database to African and Sub-Saharan African countries and extracts annual snapshots.

**Why it's necessary:** The raw AQUASTAT file has 5,841 rows spanning all countries and decades. The analysis notebooks need clean Africa- and SSA-specific CSVs at 2000 and 2021 to compute the 191% CPIS expansion headline.

**Outputs:**
- `AQUA_AfricaIrrigation.csv` — full Africa subset (1,642 rows)
- `AQUA_SSAIrrigation.csv` — SSA subset (1,397 rows)
- `AQUA_AfricaIrrigation_2000.csv` / `_2021.csv` — snapshot CSVs (49 and 53 countries)
- `AQUA_SSAIrrigation_2000.csv` / `_2021.csv` — snapshot CSVs (42 and 46 countries)

**Used by:** `1_analyze_data/0_CPIS_vs_Total.ipynb`, `1_CPIS_Africa_Map.ipynb`, `2_CPIS_by_Region.ipynb`

---

## 1_CPIS_by_Country.ipynb

**What it does:** Spatially joins the raw Chen et al. (2023) CPIS polygons to country boundaries and saves country-tagged shapefiles for Africa and SSA separately.

**Why it's necessary:** The raw CPIS dataset has no country attribute. All downstream country-level comparisons and regional breakdowns require this join.

**Outputs:**
- `Africa_CPIS_2000.shp` (8,581 polygons), `Africa_CPIS_2021.shp` (29,146 polygons)
- `SSA_CPIS_2000.shp` (7,309 polygons), `SSA_CPIS_2021.shp` (27,439 polygons)
- `1_Figure0` — side-by-side maps of CPIS footprints in 2000 vs 2021

**Used by:** `1_analyze_data/0_CPIS_vs_Total.ipynb`, `1_CPIS_Africa_Map.ipynb`, `2_CPIS_by_Region.ipynb`

---

## 2_Aridity_Refinement.ipynb

**What it does:** Clips the Global Aridity Index raster to Africa's bounding box and converts aridity class ranges into shapefiles at both continental and country levels.

**Why it's necessary:** Every spatial analysis in this project is masked to arid/semi-arid/hyper-arid regions of SSA. These shapefiles are the spatial filters applied to CPIS, dams, and AEI data throughout the pipeline.

**Outputs:**
- `Africa_Arid_Regions.tif` — clipped aridity raster
- `Africa_Continent.shp` — continent outline used for masking
- `Africa_Hyper_Arid.shp`, `Africa_Arid.shp`, `Africa_Semi_Arid.shp`, `Africa_All.shp` — aridity class polygons
- `SSA_Hyper_Arid_by_Country.shp`, `SSA_Arid_by_Country.shp`, `SSA_Semi_Arid_by_Country.shp`, `SSA_All_by_Country.shp` — country-clipped versions

**Used by:** Every subsequent preprocessing and analysis notebook.

---

## 3_GDAT_Dam_Processing.ipynb

**What it does:** Filters the GDAT global dam database to SSA irrigation dams and clips them to each aridity layer.

**Why it's necessary:** Provides the GDAT-sourced dam inventory used in initial targeting ratio analysis. Establishes that only 278 of 335 SSA irrigation dams fall in arid regions (83%), with none in hyper-arid zones.

**Outputs:**
- `Africa_Dams_Irrigation.csv` — 335 SSA irrigation dams
- `Africa_Dam_Semi_Arid.shp` (235 dams), `Africa_Dam_Arid.shp` (43 dams), `Africa_Dam_All_Arid.shp` (278 dams)

**Used by:** `1_analyze_data/3_Dams_AEI_Targeting_Ratios.ipynb`

---

## 4_CPIS_Processing.ipynb

**What it does:** Reprojects the combined CPIS dataset to EPSG:3857 and clips it to each aridity layer, adding a year column (2000/2021) to the SSA-arid subset.

**Why it's necessary:** The core water source analysis (notebooks 1–4 in `2_water_source_analysis/`) operates entirely on `SSA_Combined_CPIS_All.shp`, which is the CPIS-in-arid-SSA dataset with year labels produced here.

**Outputs:**
- `Combined_CPIS_Reproj.shp` — full reprojected CPIS
- `Combined_CPIS_Semi_Arid.shp`, `Combined_CPIS_Arid.shp`, `Combined_CPIS_Hyper_Arid.shp`, `Combined_CPIS_All.shp`
- `SSA_Combined_CPIS_All.shp` — primary input for all water source analysis notebooks

**Used by:** `1_analyze_data/` notebooks and all of `2_water_source_analysis/`.

---

## 5_GDW_Dams_Processing.ipynb

**What it does:** Loads the GDW dam database, spatially joins to arid SSA, validates ISO codes (99.8% match rate), filters to irrigation dams taller than 15 m, and summarizes dam counts by year.

**Why it's necessary:** GDW contains 2,764 dams in arid SSA — roughly 10× more than GDAT's 278. This is the primary dam dataset for elevation accessibility and anomaly detection. The 15 m height filter removes small diversions that cannot supply a CPIS. The year-by-year count (161 dams in 2000 → 168 in 2015) is the dam growth baseline.

**Outputs:**
- `GDW_Arid_SSA_Final.shp` — all 2,764 GDW dams in arid SSA
- `GDW_Arid_SSA_Final_Irr.shp` — 171 irrigation dams >15 m height

**Used by:** `1_analyze_data/3_Dams_AEI_Targeting_Ratios.ipynb`, `4_Dam_Growth_Context.ipynb`, and all of `2_water_source_analysis/`.

---

## 6_AEI_Processing.ipynb

**What it does:** Loads the Ramankutty et al. Area Equipped for Irrigation rasters for 2000 and 2015, reprojects to EPSG:3857, clips to arid SSA aridity layers, and saves masked rasters and GeoPackages.

**Why it's necessary:** The targeting ratio analysis requires knowing how much irrigated area exists within each distance band around dams — that denominator comes from the AEI rasters produced here. The 1980 baseline is also prepared for longitudinal descriptive statistics.

**Outputs:**
- `G_AEI_2015_Reprojected.gpkg`, `G_AEI_2000_Reprojected.gpkg`
- `AEI_1980_All_SSA.tif`, `AEI_2015_All_SSA.tif` — arid-masked rasters
- Aridity-layer clipped AEI shapefiles for 2000 and 2015

**Used by:** `1_analyze_data/0_CPIS_vs_Total.ipynb`, `3_Dams_AEI_Targeting_Ratios.ipynb`

---

## 7_Groundwater_Processing.ipynb

**What it does:** Converts the raw British Geological Survey / MacDonald et al. groundwater productivity xyz ASCII grid into `Groundwater_Prod.gpkg`.

**Why it's necessary:** The water-source notebooks need a reproducible groundwater input. The source map is a 5 km continental-scale grid of representative borehole yield classes in L/s, not a newly observed continuous surface.

**Input:**
- `Groundwater_Productivity_path` - raw BGS xyz ASCII productivity file, usually `xyzASCII_gwprod_v1.txt`

**Output:**
- `Groundwater_Prod_gpkg_path` - EPSG:4326 point GeoPackage with `X`, `Y`, `Liters_Second`, `productivity_class`, and `yield_range`

**Run:**

Run the notebook from top to bottom after placing the BGS xyz ASCII file at the configured raw path.

**Used by:** `2_water_source_analysis/5_groundwater_productivity_overlay.ipynb`, `6_anomaly_detection.ipynb`, and `8_spatial_statistics.ipynb`.
