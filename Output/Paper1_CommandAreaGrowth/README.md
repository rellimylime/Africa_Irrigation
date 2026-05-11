# Paper 1 Compiled Outputs

This folder contains manuscript-facing tables, figures, and diagnostics for the
command-area growth paper.

Current headline:

> 97.8% of 2000-2015 AEI growth in arid Sub-Saharan Africa occurs outside
> modeled large-dam command-area envelopes.

Use `diagnostics/paper1_manuscript_asset_manifest.csv` as the machine-readable
index of generated assets.

## Recommended Main-Text Figures

| Figure | Use |
| --- | --- |
| `figures/figure_1_growth_decomposition.png` | Main regional result: inside/outside growth, common-denominator contribution, and missing-dam tipping points. |
| `figures/figure_4_top_country_growth_contributors.png` | Country contribution and pattern check. |

## Methods Or Supplement Figures

| Figure | Use |
| --- | --- |
| `figures/figure_2_extraction_sensitivity.png` | Explains area-weighted, all-touched, and cell-center extraction; shows robustness. |
| `figures/figure_3_inside_outside_timeseries.png` | Shows inside/outside AEI over available AEI years. |
| `figures/figure_6_dem_plausibility_head_checks.png` | DEM QA: elevation-head plausibility within envelopes. |
| `figures/figure_7_reservoir_dem_sanity_check.png` | DEM QA: reservoir elevation versus dam-point DEM. |
| `figures/figure_8_missing_dam_tipping_points.png` | Standalone missing-dam tipping-point bound. |

## Tables

| Table | Purpose |
| --- | --- |
| `tables/table_1_headline_summary.csv` | One-row summary of the main result. |
| `tables/table_2_extraction_sensitivity.csv` | Robustness across extraction methods. |
| `tables/table_3_top_country_growth_contributors.csv` | Countries contributing most to positive AEI growth. |
| `tables/table_4_yearly_inside_outside_totals.csv` | Inside/outside AEI by year. |
| `tables/table_5_dem_plausibility_summary.csv` | Summary of local DEM plausibility checks. |
| `tables/table_6_missing_dam_accounting.csv` | Missing-dam growth-rate context and bound summary. |
| `tables/table_7_standardized_growth_contribution.csv` | Growth contributions using total 2000 AEI as a common denominator. |
| `tables/table_8_country_concentration_checks.csv` | Checks whether the regional result is country-dominated. |
| `tables/table_9_dam_cohort_growth_context.csv` | Existing-dam versus newly active dam footprint context. |

Markdown versions are available for most manuscript-facing tables.

## Diagnostics

| File | Purpose |
| --- | --- |
| `diagnostics/paper1_manuscript_asset_manifest.csv` | Generated asset index. |
| `diagnostics/paper1_command_area_dem_plausibility_flagged.csv` | Dam-level red-flag table from local DEM QA. |

## Source Tables

Compiled outputs are generated from:

`Data/Processed/Paper1_CommandAreaGrowth/final_tables/`

Regenerate everything with:

```bash
bash Code/paper1_command_area_growth/run_paper1_pipeline.sh
```

## Language

Use "modeled large-dam command-area envelopes." Avoid "true command areas" and
avoid treating outside-envelope growth as direct proof of groundwater irrigation.
