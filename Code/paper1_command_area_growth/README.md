# Paper 1: Command-Area Irrigation Growth

This is the canonical workflow for the paper asking:

> In arid Sub-Saharan Africa, did 2000-2015 AEI growth occur mainly inside
> modeled large-dam command-area envelopes, or outside them?

## Headline

Using the primary area-weighted extraction, 97.8% of 2000-2015 AEI growth occurs
outside the modeled large-dam command-area envelopes. The result is stable across
area-weighted, all-touched, and cell-center extraction variants.

Key values from the current run:

| Quantity | Value |
| --- | ---: |
| Study period | 2000-2015 |
| Panel countries | 46 |
| Total AEI growth | 533,428 ha |
| Growth inside modeled envelopes | 11,881 ha |
| Growth outside modeled envelopes | 521,548 ha |
| Outside-growth share | 97.77% |
| Extraction sensitivity range | 97.28-97.77% outside |
| Active 2015 command-area dams | 169 |
| Active 2015 command-area footprint | 994,364 ha |

## What This Workflow Measures

The measured outcome is gridded AEI growth from 2000 to 2015.

The exposure is a yearly version of the modeled command-area envelope layer:
for each AEI year, the workflow keeps command-area polygons attached to dams
commissioned by that year, then dissolves overlaps so an AEI pixel can only be
counted once.

The result should be interpreted as growth inside or outside modeled large-dam
command-area envelopes. It is not a map of true observed irrigation service
boundaries and it is not a complete attribution of irrigation water source.

## Main Caveats

**Command areas are modeled envelopes.** The source layer is a physical proxy,
not surveyed command-area boundaries. Use the phrase "modeled large-dam
command-area envelopes."

**DEM QA raises concerns.** The local HDMA-derived DEM check flags many active
2015 envelopes as including terrain above reservoir elevation +10 m. Reservoir
elevation metadata look broadly sane at dam points, but envelope geometry should
be caveated and audited in GEE with the exact DEM/export logic used to create the
layer.

**Dam coverage is incomplete.** GDW and the command-area export are best treated
as documented large, reservoir-forming dams, not all water-control
infrastructure. Missing-dam accounting is reported as a tipping-point bound:
missing dams would need to explain about 41,500 ha of currently outside growth
to lower the outside-growth share below 90%, 121,500 ha to lower it below 75%,
and 254,800 ha to lower it below 50%.

## Run The Pipeline

From the repository root:

```bash
bash Code/paper1_command_area_growth/run_paper1_pipeline.sh
```

PowerShell:

```powershell
.\Code\paper1_command_area_growth\run_paper1_pipeline.ps1
```

Set `PYTHON` if `python` is not the project environment:

```bash
PYTHON=/path/to/python bash Code/paper1_command_area_growth/run_paper1_pipeline.sh
```

The detailed operational checklist is in `RUNBOOK.md`.

## Script Order

| Step | Script | Role |
| --- | --- | --- |
| 00 | `00_prepare_paper_inputs.py` | Validate/build the arid-SSA mask and GDW dam layers needed by Paper 1. |
| 01 | `01_prepare_yearly_command_areas.py` | Build active, overlap-free command-area layers by AEI year. |
| 02 | `02_extract_irrigation_inside_outside.py` | Extract AEI inside/outside command areas by country and year. |
| 03 | `03_growth_decomposition.py` | Decompose 2000-2015 AEI growth into inside/outside components. |
| 04 | `04_qa_sensitivity_tables.py` | Write input QA and extraction-method sensitivity tables. |
| 05 | `05_make_paper1_figures_tables.py` | Build manuscript-facing figures, tables, and the asset manifest. |
| 06 | `06_validate_command_area_dem_plausibility.py` | Run local DEM plausibility checks for command-area envelopes. |
| 07 | `07_missing_dam_accounting.py` | Report missing-dam growth-rate context and tipping-point bounds. |

## Output Locations

| Location | Contents |
| --- | --- |
| `Data/Processed/Paper1_CommandAreaGrowth/yearly_command_areas/` | Active dissolved command-area layers by year. |
| `Data/Processed/Paper1_CommandAreaGrowth/extracted_irrigation/` | Raster extraction diagnostics and intermediate outputs. |
| `Data/Processed/Paper1_CommandAreaGrowth/final_tables/` | Canonical analytical CSVs used by paper assets. |
| `Output/Paper1_CommandAreaGrowth/tables/` | Manuscript-facing tables. |
| `Output/Paper1_CommandAreaGrowth/figures/` | Manuscript-facing figures. |
| `Output/Paper1_CommandAreaGrowth/diagnostics/` | Asset manifest and QA red-flag tables. |

## Figure Use

Recommended main-text results figures:

1. `figure_1_growth_decomposition.png` - regional decomposition, common-denominator
   growth contribution, and missing-dam tipping points.
2. `figure_4_top_country_growth_contributors.png` - country contributors and
   pattern checks.

Recommended methods/supplement figures:

- `figure_2_extraction_sensitivity.png` - extraction-method diagram and
  sensitivity result.
- `figure_3_inside_outside_timeseries.png` - AEI time series.
- `figure_6_dem_plausibility_head_checks.png` and
  `figure_7_reservoir_dem_sanity_check.png` - DEM QA.
- `figure_8_missing_dam_tipping_points.png` - standalone missing-dam bound.

## Supporting Evidence

`Code/2_water_source_analysis/` contains supporting CPIS/water-source analyses:
activity classification, DEM accessibility, groundwater productivity,
dam-explained classification, anomaly detection, and spatial statistics. Treat
these as interpretation, not as the primary measured outcome.
