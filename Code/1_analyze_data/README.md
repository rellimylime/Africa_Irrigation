# 1_analyze_data

This folder contains notebooks that analyze irrigation and center pivot irrigation system (CPIS) expansion between 2000 and 2021, using processed datasets prepared in `Code/0_process_data`.

## Contents

- **0_CPIS_vs_Total.ipynb**  
  Compares overall irrigation area growth with CPIS growth for Africa and Sub-Saharan Africa. Produces summary figures and percent-change calculations.

- **1_CPIS_Africa_Map.ipynb**  
  Maps CPIS share of total irrigation at the country level in 2000 and 2021. Includes masking to SSA and aridity regions.

- **2_CPIS_by_Region.ipynb**  
  Breaks down CPIS shares by region and aridity classes, using outputs from the Africa map notebook.

- **3_Dams_AEI_Targeting_Ratios.ipynb**  
  (transition notebook – located here for convenience, but part of the dam analysis workflow) Calculates CPIS targeting ratios relative to dam proximity in different aridity zones.

- **4_Groundwater.ipynb**  
  (transition notebook – also part of the dam analysis workflow) Explores the relationship between groundwater productivity and CPIS siting.

## Inputs

- Processed irrigation area tables (from AQUASTAT).  
- CPIS shapefiles for 2000 and 2021, clipped and processed to Africa.  
- Africa/SSA boundaries and aridity rasters.  
- Outputs from notebooks in `Code/0_process_data`.

All dataset paths are configured in `config.yaml`.

## Outputs

- Figures in `Output/Analyze/` (growth plots, maps, regional comparisons).  
- Tables of irrigated area, CPIS area, and CPIS share by country and region.  

## Notes

- For reproducibility, run the preprocessing notebooks in `Code/0_process_data` first.  
- This folder’s analyses focus primarily on spatial and temporal comparisons of irrigation and CPIS; dam- and groundwater-specific analyses are described in more detail in `Code/2_dam_analysis`.
