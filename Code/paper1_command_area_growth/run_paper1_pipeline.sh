#!/usr/bin/env bash
set -euo pipefail

# Use `PYTHON=/path/to/python bash Code/paper1_command_area_growth/run_paper1_pipeline.sh`
# if `python` is not the project environment on your machine.
PYTHON_BIN="${PYTHON:-python}"

run_step() {
  local label="$1"
  shift
  echo
  echo "== ${label} =="
  "${PYTHON_BIN}" "$@"
}

run_step "00 prepare paper inputs" Code/paper1_command_area_growth/00_prepare_paper_inputs.py
run_step "01 prepare yearly command areas" Code/paper1_command_area_growth/01_prepare_yearly_command_areas.py --command-area No_Crop_Vectorized_Command_Area_shp_path --overwrite
run_step "02 extract AEI inside/outside" Code/paper1_command_area_growth/02_extract_irrigation_inside_outside.py --area-weighted
run_step "03 decompose 2000-2015 growth" Code/paper1_command_area_growth/03_growth_decomposition.py --base-year 2000 --end-year 2015
run_step "04 build QA and sensitivity tables" Code/paper1_command_area_growth/04_qa_sensitivity_tables.py
run_step "05 build manuscript figures and tables" Code/paper1_command_area_growth/05_make_paper1_figures_tables.py
run_step "06 run DEM plausibility QA" Code/paper1_command_area_growth/06_validate_command_area_dem_plausibility.py
run_step "07 run missing-dam accounting" Code/paper1_command_area_growth/07_missing_dam_accounting.py
