# 2_water_source_analysis

These files are supporting evidence for the command-area growth paper, not the main paper workflow.

The paper's primary question is answered in `Code/paper1_command_area_growth/`: did irrigation expansion occur inside modeled large-dam command areas or outside them? The notebooks here help interpret outside-command-area irrigation by asking whether CPIS could plausibly use dam water, groundwater, or another source.

Use these analyses carefully: "outside command area" is the paper's primary spatial classification; water-source attribution is supporting evidence and should not be treated as proven for every field.

## Pipeline

Run in order:

1. `1_download_hdma_africa.py`
2. `2_ndwi_analysis.ipynb`
3. `3_preprocess_hdma_elevation.py`
4. `4_dem_flow_analysis.ipynb`
5. `5_groundwater_productivity_overlay.ipynb`
6. `6_anomaly_detection.ipynb` (legacy exploratory check)
7. `7_dam_explained_irrigation_classification.ipynb`
8. `8_spatial_statistics.ipynb`

The download step pulls the HDMA Africa DEM and flow-direction ZIP tiles into `Data/Raw/HDMA_Africa/`. The preprocessing step builds `Data/Processed/Africa_Elevation_Reprojected.tif`, which the downstream elevation-aware notebooks use.
The old PowerShell and shell wrappers have been removed so the download step now has a single Python entry point.

For reproducibility, run the downloader from the same Python environment you use for the notebooks, keep `config.yaml` unchanged, and make sure any proxy/VPN settings are the same as when the data were first downloaded. The HDMA ZIPs are large, so the downloader discovers the attached-file URLs from ScienceBase metadata, writes resumable `.part` files, and validates each completed ZIP before renaming it.

Useful download commands:

```powershell
# Smoke test the already-used Africa processing unit before downloading everything
python Code/2_water_source_analysis/1_download_hdma_africa.py --layers DEM FD --units 5_4

# Check ScienceBase/VPN/proxy access without downloading large files
python Code/2_water_source_analysis/1_download_hdma_africa.py --layers DEM --units 0 --check-only

# Download all 19 DEM and flow-direction units
python Code/2_water_source_analysis/1_download_hdma_africa.py --layers DEM FD
```

If ScienceBase is only reachable through a proxy, pass it explicitly with `--proxy`. To preview the files and URLs without contacting ScienceBase, add `--dry-run`.

## 2_ndwi_analysis.ipynb

Computes NDWI from Sentinel-2 bands B03 and B8A over each CPIS polygon and classifies systems as actively irrigated or inactive.

Outputs:
- `NDWI_output_tif_path`
- `Active_CPIS_shp_path`
- `Inactive_CPIS_shp_path`
- `CPIS_NDWI_stats_csv_path`

## 3_preprocess_hdma_elevation.py

Builds the projected Africa DEM crop from the HDMA Africa DEM tiles and writes `Africa_Elevation_Reprojected_tif_path`.

Inputs:
- `Africa_HDMA_DEM_zip_dir_path`
- `SSA_All_by_Country_shp_path`

Output:
- `Africa_Elevation_Reprojected_tif_path`

## 4_dem_flow_analysis.ipynb

Samples elevation at each CPIS centroid and its nearest dam, then classifies each CPIS as feasible, infeasible by elevation, or infeasible by distance. RichDEM is used to compute D8 flow direction on a subsampled DEM.

Outputs:
- `CPIS_Elevation_Classified_shp_path`
- `Dam_CPIS_Profiles_csv_path`

## 5_groundwater_productivity_overlay.ipynb

Assigns BGS / MacDonald et al. groundwater productivity to each CPIS centroid. The direct nearest-source-map value is the primary groundwater indicator because the source data are categorical yield classes rather than continuous well observations.

Required preprocessing:
- `Code/0_process_data/7_Groundwater_Processing.ipynb` builds `Groundwater_Prod_gpkg_path` from the raw BGS xyz ASCII file configured as `Groundwater_Productivity_path`.

Outputs:
- `CPIS_GP_Groundwater_csv_path` with `source_gw_productivity`, `productivity_class`, and `yield_range`

## 6_anomaly_detection.ipynb

Legacy exploratory Isolation Forest workflow for identifying CPIS outliers. Retained for provenance, but it should not be treated as the main answer to the inside-vs-outside dam infrastructure question.

Outputs:
- `CPIS_Feature_Matrix_csv_path`
- `CPIS_Anomaly_Scores_csv_path`
- `CPIS_Anomalies_shp_path`

## 7_dam_explained_irrigation_classification.ipynb

Classifies each CPIS by whether it is plausibly explained by large-dam access using distance to nearest dam and elevation feasibility. Groundwater productivity and NDWI activity are joined afterward as interpretive context, not as criteria for the dam-explained classification.

Outputs:
- `CPIS_Dam_Explained_csv_path`
- `CPIS_Dam_Explained_shp_path`

## 8_spatial_statistics.ipynb

Runs the cross-K function, geographically weighted regression, and D8 flow-path connectivity analysis to complement the simpler targeting-ratio story.

Outputs:
- `CPIS_GWR_Results_csv_path`
- `CPIS_Flow_Connectivity_shp_path`
