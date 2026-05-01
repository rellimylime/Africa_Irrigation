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
  to a dam commissioned by that year.
- `outside command area` means outside those modeled areas. It is evidence of
  irrigation not explained by the modeled large-dam command-area layer, not proof
  of groundwater use.
- CPIS, NDVI/NDWI activity, groundwater productivity, DEM accessibility, and
  flow-connectivity analyses are supporting evidence.

## Run Order

From the repository root:

```powershell
python Code/paper1_command_area_growth/00_prepare_paper_inputs.py
python Code/paper1_command_area_growth/01_prepare_yearly_command_areas.py --overwrite
python Code/paper1_command_area_growth/02_extract_irrigation_inside_outside.py --all-touched
python Code/paper1_command_area_growth/03_growth_decomposition.py
```

Wrapper commands:

```bash
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

## Current Blockers To Resolve

The scripts are intentionally strict. If they stop early, use the error message
as the next acquisition/preprocessing task.

Known likely blockers from the repository audit:

- If starting from raw-only data, `00_prepare_paper_inputs.py` now rebuilds the
  SSA arid country mask and GDW processed dam layers when they are missing.
- Command-area polygons and AEI rasters are direct inputs. They are validated but
  not transformed before Paper 1 processing.
- The paper final tables remain placeholders until the scripts above run.

## Recommended Paper Framing

Use `2000-2015` for total-AEI command-area growth unless a credible 2020/2021 AEI
surface is added. Use `2000-2021` for CPIS expansion and continued-use supporting
evidence. Do not mix those date ranges in a single headline without a clear caveat.
