$ErrorActionPreference = "Stop"

if ($env:PYTHON) {
    $PythonBin = $env:PYTHON
} else {
    $PythonBin = "python"
}

function Invoke-PaperStep {
    param(
        [string]$Label,
        [string]$Script,
        [string[]]$Arguments = @()
    )

    Write-Host ""
    Write-Host "== $Label =="
    & $PythonBin $Script @Arguments
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Invoke-PaperStep "00 prepare paper inputs" "Code/paper1_command_area_growth/00_prepare_paper_inputs.py"
Invoke-PaperStep "01 prepare yearly command areas" "Code/paper1_command_area_growth/01_prepare_yearly_command_areas.py" @("--command-area", "No_Crop_Vectorized_Command_Area_shp_path", "--overwrite")
Invoke-PaperStep "02 extract AEI inside/outside" "Code/paper1_command_area_growth/02_extract_irrigation_inside_outside.py" @("--area-weighted")
Invoke-PaperStep "03 decompose 2000-2015 growth" "Code/paper1_command_area_growth/03_growth_decomposition.py" @("--base-year", "2000", "--end-year", "2015")
Invoke-PaperStep "04 build QA and sensitivity tables" "Code/paper1_command_area_growth/04_qa_sensitivity_tables.py"
Invoke-PaperStep "05 build manuscript figures and tables" "Code/paper1_command_area_growth/05_make_paper1_figures_tables.py"
Invoke-PaperStep "06 run DEM plausibility QA" "Code/paper1_command_area_growth/06_validate_command_area_dem_plausibility.py"
Invoke-PaperStep "07 run missing-dam accounting" "Code/paper1_command_area_growth/07_missing_dam_accounting.py"
