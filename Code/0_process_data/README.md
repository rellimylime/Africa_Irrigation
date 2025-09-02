# Africa Irrigation Data Processing

This directory contains Jupyter notebooks and scripts for processing, analyzing, and visualizing irrigation, dam, aridity, and groundwater data for Sub-Saharan Africa. Each notebook is organized by data type and workflow step, with clear documentation and modular code.

## Workflow Overview

1. **Aridity Refinement** (`2_Aridity_Refinement.ipynb`)
	- Trims global aridity raster to Africa's extent
	- Extracts continent outline and generates aridity region shapefiles
	- Creates country-level arid region shapefiles for Sub-Saharan Africa

2. **GDAT Dam Processing** (`3_GDAT_Dam_Processing.ipynb`)
	- Filters global dam dataset for Sub-Saharan Africa and irrigation purpose
	- Converts filtered dams to GeoDataFrame and spatially trims to arid regions
	- Saves results for each aridity class as shapefiles

3. **CPIS Processing** (`4_CPIS_Processing.ipynb`)
	- Trims and reprojects CPIS data into aridity layers
	- Filters the 'All' layer to Sub-Saharan Africa and adds year information

4. **GDW Dams Processing** (`5_GDW_Dams_Processing.ipynb`)
	- Loads and spatially joins GDW dam and arid region data
	- Validates ISO matching and saves arid SSA dams
	- Filters for irrigation dams and summarizes dam counts by year

5. **AEI (Area Equipped for Irrigation) Processing** (`6_AEI_Processing.ipynb`)
	- Loads, crops, and reprojects AEI raster data for 2015 and 2000
	- Crops AEI data to different aridity layers
	- Processes and clips 1980 AEI data to arid region
	- Rasterizes arid-masked polygons and visualizes processed AEI data

6. **Groundwater Productivity Processing** (`7_GW_Processing.ipynb`)
	- Loads and processes groundwater productivity data
	- Maps productivity categories to numeric values
	- Previews processed data

## How to Use

1. Open each notebook in order to follow the data processing workflow.
2. Each notebook begins with a summary and step-by-step documentation in markdown cells.
3. Outputs (shapefiles, GeoPackages, CSVs, and visualizations) are saved to the appropriate directories as specified in the configuration files.

## Directory Structure

- `2_Aridity_Refinement.ipynb` — Aridity raster and shapefile processing
- `3_GDAT_Dam_Processing.ipynb` — Global dam data filtering and spatial analysis
- `4_CPIS_Processing.ipynb` — CPIS dataset processing and SSA extraction
- `5_GDW_Dams_Processing.ipynb` — GDW dam data spatial join and filtering
- `6_AEI_Processing.ipynb` — AEI raster processing and clipping
- `7_GW_Processing.ipynb` — Groundwater productivity data processing
- `utils/` — Utility functions for spatial and general data operations

## Requirements

- Python 3.8+
- Jupyter Notebook
- Key packages: `geopandas`, `rasterio`, `matplotlib`, `shapely`, `pandas`, `tqdm`
- See `requirements.yml` for full environment specification

## Notes

- All notebooks are modular and documented for clarity.
- Outputs are saved in standardized formats for downstream analysis and mapping.
- For questions or contributions, please open an issue or pull request.
