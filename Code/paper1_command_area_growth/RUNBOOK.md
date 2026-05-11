# Paper 1 Workflow Runbook

This runbook is the operational checklist for regenerating the command-area
growth paper outputs. For the scientific framing, see `README.md`. For the
command-area source decision, see `COMMAND_AREA_SOURCE.md`.

## Before Running

Confirm these inputs are configured in `config.yaml`:

- AEI rasters for 2000 and 2015, plus any intermediate AEI years used in the
  time-series panel.
- `No_Crop_Vectorized_Command_Area_shp_path`, currently pointing to
  `Data/Raw/Physical_Envelope_Command_Areas_AnyUse_Hgt15-shp`.
- Arid-SSA country mask inputs.
- GDW dam data with commissioning year, height, irrigation-use fields, and
  reservoir metadata.
- Local HDMA-derived DEM if running the DEM plausibility step.

Run from the repository root.

## Full Pipeline

```bash
bash Code/paper1_command_area_growth/run_paper1_pipeline.sh
```

PowerShell:

```powershell
.\Code\paper1_command_area_growth\run_paper1_pipeline.ps1
```

If needed, pin the Python executable:

```bash
PYTHON=/path/to/python bash Code/paper1_command_area_growth/run_paper1_pipeline.sh
```

## Individual Steps

```powershell
python Code/paper1_command_area_growth/00_prepare_paper_inputs.py
python Code/paper1_command_area_growth/01_prepare_yearly_command_areas.py --command-area No_Crop_Vectorized_Command_Area_shp_path --overwrite
python Code/paper1_command_area_growth/02_extract_irrigation_inside_outside.py --area-weighted
python Code/paper1_command_area_growth/03_growth_decomposition.py --base-year 2000 --end-year 2015
python Code/paper1_command_area_growth/04_qa_sensitivity_tables.py
python Code/paper1_command_area_growth/05_make_paper1_figures_tables.py
python Code/paper1_command_area_growth/06_validate_command_area_dem_plausibility.py
python Code/paper1_command_area_growth/07_missing_dam_accounting.py
```

## Expected Final Outputs

Analytical source tables:

- `Data/Processed/Paper1_CommandAreaGrowth/final_tables/inside_outside_irrigation_by_country_year_area_weighted.csv`
- `Data/Processed/Paper1_CommandAreaGrowth/final_tables/growth_decomposition_by_country_area_weighted.csv`
- `Data/Processed/Paper1_CommandAreaGrowth/final_tables/growth_decomposition_summary_area_weighted.csv`
- `Data/Processed/Paper1_CommandAreaGrowth/final_tables/paper1_extraction_sensitivity_summary.csv`
- `Data/Processed/Paper1_CommandAreaGrowth/final_tables/paper1_command_area_dem_plausibility_summary.csv`
- `Data/Processed/Paper1_CommandAreaGrowth/final_tables/paper1_missing_dam_tipping_points.csv`

Compiled manuscript outputs:

- `Output/Paper1_CommandAreaGrowth/tables/table_1_headline_summary.csv`
- `Output/Paper1_CommandAreaGrowth/tables/table_2_extraction_sensitivity.csv`
- `Output/Paper1_CommandAreaGrowth/tables/table_3_top_country_growth_contributors.csv`
- `Output/Paper1_CommandAreaGrowth/tables/table_4_yearly_inside_outside_totals.csv`
- `Output/Paper1_CommandAreaGrowth/tables/table_5_dem_plausibility_summary.csv`
- `Output/Paper1_CommandAreaGrowth/tables/table_6_missing_dam_accounting.csv`
- `Output/Paper1_CommandAreaGrowth/tables/table_7_standardized_growth_contribution.csv`
- `Output/Paper1_CommandAreaGrowth/tables/table_8_country_concentration_checks.csv`
- `Output/Paper1_CommandAreaGrowth/tables/table_9_dam_cohort_growth_context.csv`
- `Output/Paper1_CommandAreaGrowth/figures/figure_1_growth_decomposition.png`
- `Output/Paper1_CommandAreaGrowth/figures/figure_2_extraction_sensitivity.png`
- `Output/Paper1_CommandAreaGrowth/figures/figure_3_inside_outside_timeseries.png`
- `Output/Paper1_CommandAreaGrowth/figures/figure_4_top_country_growth_contributors.png`
- `Output/Paper1_CommandAreaGrowth/figures/figure_6_dem_plausibility_head_checks.png`
- `Output/Paper1_CommandAreaGrowth/figures/figure_7_reservoir_dem_sanity_check.png`
- `Output/Paper1_CommandAreaGrowth/figures/figure_8_missing_dam_tipping_points.png`
- `Output/Paper1_CommandAreaGrowth/diagnostics/paper1_manuscript_asset_manifest.csv`
- `Output/Paper1_CommandAreaGrowth/diagnostics/paper1_command_area_dem_plausibility_flagged.csv`

## Interpretation Checks

- The 2000-2015 headline should use the area-weighted extraction.
- Extraction sensitivity should stay near 97.3-97.8% outside growth.
- DEM QA is a caveat check, not validation of true command-area boundaries.
- Missing-dam accounting should be framed mainly as a tipping-point bound, not as
  proof that dam-associated irrigation is losing mode share.

## Troubleshooting

- If a script stops on a missing input, update `config.yaml` or regenerate the
  upstream processed layer named in the error.
- If `python` points to the wrong environment, set `PYTHON` before running the
  wrapper.
- If manuscript tables or figures look stale, rerun steps `05` through `07`;
  those steps rebuild compiled outputs and update the asset manifest.
