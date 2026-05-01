#!/usr/bin/env bash
set -euo pipefail

# Use `PYTHON=/path/to/python bash Code/paper1_command_area_growth/run_paper1_pipeline.sh`
# if `python` is not the project environment on your machine.
PYTHON_BIN="${PYTHON:-python}"

"${PYTHON_BIN}" Code/paper1_command_area_growth/00_prepare_paper_inputs.py
"${PYTHON_BIN}" Code/paper1_command_area_growth/01_prepare_yearly_command_areas.py --overwrite
"${PYTHON_BIN}" Code/paper1_command_area_growth/02_extract_irrigation_inside_outside.py --all-touched
"${PYTHON_BIN}" Code/paper1_command_area_growth/03_growth_decomposition.py

