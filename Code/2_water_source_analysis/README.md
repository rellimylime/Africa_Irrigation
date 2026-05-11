# 2_water_source_analysis

These analyses support interpretation of outside-command-area irrigation. They
are not the primary Paper 1 workflow.

Primary Paper 1 question:

> Did AEI growth occur inside or outside modeled large-dam command-area
> envelopes?

This folder asks follow-up questions about CPIS activity, topographic dam
access, groundwater context, and spatial patterning.

## Use With Care

- "Outside command area" is the main paper classification.
- Water-source attribution here is interpretive support, not field-level proof.
- The anomaly workflow is retained for provenance and should not be treated as
  the main answer.

## Notebook Order

| Step | File | Status | Purpose |
| --- | --- | --- | --- |
| 1 | `1_download_hdma_africa.py` | Supporting | Download HDMA Africa DEM and flow-direction tiles. |
| 2 | `2_ndwi_analysis.ipynb` | Supporting | Classify CPIS activity from Sentinel-2 water/vegetation index outputs. |
| 3 | `3_preprocess_hdma_elevation.py` | Supporting | Build the projected Africa DEM crop. |
| 4 | `4_dem_flow_analysis.ipynb` | Supporting | Classify CPIS by distance/elevation feasibility relative to nearest dam. |
| 5 | `5_groundwater_productivity_overlay.ipynb` | Supporting | Attach BGS/MacDonald groundwater productivity classes to CPIS. |
| 6 | `6_anomaly_detection.ipynb` | Legacy | Exploratory Isolation Forest outlier workflow. |
| 7 | `7_dam_explained_irrigation_classification.ipynb` | Supporting | Classify CPIS as dam-accessible proxy, near-dam-but-uphill, distant, or unknown. |
| 8 | `8_spatial_statistics.ipynb` | Supporting | Cross-K, GWR, and flow-connectivity analyses. |

## Key Outputs

| Output key | Meaning |
| --- | --- |
| `Active_CPIS_shp_path` / `Inactive_CPIS_shp_path` | Activity-classified CPIS polygons. |
| `CPIS_NDWI_stats_csv_path` | Per-CPIS activity index statistics. |
| `Africa_Elevation_Reprojected_tif_path` | Projected HDMA-derived DEM. |
| `CPIS_Elevation_Classified_shp_path` | CPIS distance/elevation classes relative to nearest dam. |
| `Dam_CPIS_Profiles_csv_path` | Pairwise dam-CPIS distance and elevation statistics. |
| `CPIS_GP_Groundwater_csv_path` | Groundwater productivity class/value at each CPIS centroid. |
| `CPIS_Dam_Explained_csv_path` | Dam-explained / least-dam-explained CPIS classification. |
| `CPIS_GWR_Results_csv_path` | GWR local fit and coefficient outputs. |
| `CPIS_Flow_Connectivity_shp_path` | D8 flow-path connectivity output. |

All paths are configured in `config.yaml`.

## Relationship To Paper 1

Use these analyses to discuss plausible mechanisms for outside-envelope growth:
small reservoirs, diversions, pumps, groundwater, or other decentralized water
access. Do not use them to replace the Paper 1 inside/outside AEI decomposition.

Legacy generated dam-analysis outputs from earlier versions of this workflow are
preserved under `Output/Archive/Dam_Analysis/`. New generated outputs should not
be written inside `Code/`.
