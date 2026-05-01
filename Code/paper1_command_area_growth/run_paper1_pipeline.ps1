$ErrorActionPreference = "Stop"

if ($env:PYTHON) {
    $PythonBin = $env:PYTHON
} else {
    $PythonBin = "python"
}

& $PythonBin Code/paper1_command_area_growth/00_prepare_paper_inputs.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $PythonBin Code/paper1_command_area_growth/01_prepare_yearly_command_areas.py --overwrite
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $PythonBin Code/paper1_command_area_growth/02_extract_irrigation_inside_outside.py --all-touched
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $PythonBin Code/paper1_command_area_growth/03_growth_decomposition.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

