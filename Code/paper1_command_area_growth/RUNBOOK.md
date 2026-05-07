# Paper 1 Workflow Runbook

This folder now has a script-first canonical workflow. The notebooks can call
these scripts later, but the paper results should come from the stable files
written under `Data/Processed/Paper1_CommandAreaGrowth/final_tables/`.

## Research Estimand

Primary estimand:

> For arid Sub-Saharan Africa, what share of gridded AEI growth occurred inside
> modeled large-dam command areas versus outside those command areas?

Interpretation rule:

- `inside command area` means spatially inside a modeled command area attached
  to a dam commissioned by that year and not removed by that year. The local GDW
  copy has a `REM_YEAR` field, but the current arid-SSA records use the missing
  value `-99`, so no dams are excluded as decommissioned in the present run.
- The main command-area source is `No_Crop_Vectorized_Command_Area_shp_path`,
  currently expected to point to
  `Physical_Envelope_Command_Areas_AnyUse_Hgt15`. The Initial and All-Height
  Initial exports are retained for sensitivity checks, not as the default paper
  source.
- The primary source should remain the physical-envelope final export. It does
  not condition the command-area geometry on 2019 cropland, so the
  infrastructure mask is not mechanically defined by a late-period land-cover
  outcome. The yearly builder now stops on an unverified final/vectorized source
  unless explicitly allowed for exploratory runs.
- Dam inclusion should mean irrigation is any listed GDW use. The local dam layer
  uses `USE_IRRI` when present, but the GEE command-area export must be
  regenerated with the same any-use filter before final paper results. The
  superseded `No_Crop_Vectorized_Command_Areas_AnyUse_Hgt15` export is not
  acceptable for final results because it produced only 24 records and a tiny
  command-area footprint. The strict pure-no-crop
  `No_Crop_Vectorized_Command_Areas_AnyUse_Hgt15_ModelUnits` export is a
  sensitivity run only because it produced only 27 records.
- `outside command area` means outside those modeled areas. It is evidence of
  irrigation not explained by the modeled large-dam command-area layer, not proof
  of groundwater use.
- CPIS, NDVI/NDWI activity, groundwater productivity, DEM accessibility, and
  flow-connectivity analyses are supporting evidence.

## Run Order

From the repository root:

```powershell
python Code/paper1_command_area_growth/00_prepare_paper_inputs.py
python Code/paper1_command_area_growth/01_prepare_yearly_command_areas.py --command-area No_Crop_Vectorized_Command_Area_shp_path --overwrite
python Code/paper1_command_area_growth/02_extract_irrigation_inside_outside.py --area-weighted
python Code/paper1_command_area_growth/03_growth_decomposition.py --base-year 2000 --end-year 2015
python Code/paper1_command_area_growth/04_qa_sensitivity_tables.py
python Code/paper1_command_area_growth/05_make_paper1_figures_tables.py
python Code/paper1_command_area_growth/06_validate_command_area_dem_plausibility.py
```

Wrapper commands:

```bash
bash Code/paper1_command_area_growth/run_paper1_pipeline.sh
```

In Git Bash on Windows, activate the project conda environment first:

```bash
cd /c/Users/ermil/Documents/Africa_Irrigation
source ~/miniconda3/etc/profile.d/conda.sh
conda activate irrigation
bash Code/paper1_command_area_growth/run_paper1_pipeline.sh
```

```powershell
.\Code\paper1_command_area_growth\run_paper1_pipeline.ps1
```

The current local machine may need the project conda environment activated first.

## Outputs

- `Data/Processed/SSA_All_Arid_by_Country-shp/SSA_All_Arid_by_Country.shp`
- `Data/Processed/GDW_Arid_SSA_Final-shp/GDW_Arid_SSA_Final.shp`
- `Data/Processed/GDW_Arid_SSA_Final-shp/GDW_Arid_SSA_Final_Irr.shp`
- `yearly_command_areas/command_areas_<year>.gpkg`
- `final_tables/yearly_command_area_inventory.csv`
- `final_tables/inside_outside_irrigation_by_country_year.csv`
- `extracted_irrigation/inside_outside_extraction_diagnostics.csv`
- `final_tables/growth_decomposition_by_country.csv`
- `final_tables/growth_decomposition_summary.csv`
- `final_tables/paper1_input_qa_summary.csv`
- `final_tables/paper1_yearly_command_area_qa.csv`
- `final_tables/paper1_extraction_sensitivity_summary.csv`
- `Output/Paper1_CommandAreaGrowth/tables/table_*.csv`
- `Output/Paper1_CommandAreaGrowth/tables/table_*.md`
- `Output/Paper1_CommandAreaGrowth/figures/figure_*.png`
- `Output/Paper1_CommandAreaGrowth/diagnostics/paper1_manuscript_asset_manifest.csv`
- `final_tables/paper1_command_area_dem_plausibility_by_dam.csv`
- `final_tables/paper1_command_area_dem_plausibility_summary.csv`
- `Output/Paper1_CommandAreaGrowth/diagnostics/paper1_command_area_dem_plausibility_flagged.csv`

## Current Blockers To Resolve

The scripts are intentionally strict. If they stop early, use the error message
as the next acquisition/preprocessing task.

Known likely blockers from the repository audit:

- If starting from raw-only data, `00_prepare_paper_inputs.py` now rebuilds the
  SSA arid country mask and GDW processed dam layers when they are missing.
- Command-area polygons and AEI rasters are direct inputs. They are validated but
  not transformed before Paper 1 processing.
- Manuscript tables and figures are regenerated by `05_make_paper1_figures_tables.py`
  from the checked final tables; edit the script rather than hand-editing outputs.
- DEM plausibility checks are QA checks against the local DEM, not ground-truth
  command-area validation. Treat flags as evidence to revisit or caveat the
  command-area envelope model.

## Recommended Paper Framing

Use `2000-2015` for total-AEI command-area growth unless a credible 2020/2021 AEI
surface is added. Use `2000-2021` for CPIS expansion and continued-use supporting
evidence. Do not mix those date ranges in a single headline without a clear caveat.
