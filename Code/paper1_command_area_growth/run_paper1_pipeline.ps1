$ErrorActionPreference = "Stop"

if ($env:PYTHON) {
    $PythonBin = $env:PYTHON
} else {
    $PythonBin = "python"
}

& $PythonBin Code/paper1_command_area_growth/00_prepare_paper_inputs.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $PythonBin Code/paper1_command_area_growth/01_prepare_yearly_command_areas.py --command-area No_Crop_Vectorized_Command_Area_shp_path --overwrite
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $PythonBin Code/paper1_command_area_growth/02_extract_irrigation_inside_outside.py --area-weighted
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $PythonBin Code/paper1_command_area_growth/03_growth_decomposition.py --base-year 2000 --end-year 2015
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $PythonBin Code/paper1_command_area_growth/04_qa_sensitivity_tables.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $PythonBin Code/paper1_command_area_growth/05_make_paper1_figures_tables.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $PythonBin Code/paper1_command_area_growth/06_validate_command_area_dem_plausibility.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
