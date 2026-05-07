#!/usr/bin/env bash
set -euo pipefail

# Use `PYTHON=/path/to/python bash Code/paper1_command_area_growth/run_paper1_pipeline.sh`
# if `python` is not the project environment on your machine.
PYTHON_BIN="${PYTHON:-python}"

"${PYTHON_BIN}" Code/paper1_command_area_growth/00_prepare_paper_inputs.py
"${PYTHON_BIN}" Code/paper1_command_area_growth/01_prepare_yearly_command_areas.py --command-area No_Crop_Vectorized_Command_Area_shp_path --overwrite
"${PYTHON_BIN}" Code/paper1_command_area_growth/02_extract_irrigation_inside_outside.py --area-weighted
"${PYTHON_BIN}" Code/paper1_command_area_growth/03_growth_decomposition.py --base-year 2000 --end-year 2015
"${PYTHON_BIN}" Code/paper1_command_area_growth/04_qa_sensitivity_tables.py
"${PYTHON_BIN}" Code/paper1_command_area_growth/05_make_paper1_figures_tables.py
"${PYTHON_BIN}" Code/paper1_command_area_growth/06_validate_command_area_dem_plausibility.py
