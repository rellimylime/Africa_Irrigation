# Code

This directory contains the analysis code for the Africa irrigation project.
The paper workflow is now script-first; notebooks outside that workflow are
supporting or legacy material.

## Directory Guide

| Directory | Status | Purpose |
| --- | --- | --- |
| `paper1_command_area_growth/` | Primary | Canonical Paper 1 workflow for AEI growth inside/outside modeled large-dam command-area envelopes. |
| `0_process_data/` | Supporting/older | Raw-data preprocessing notebooks used by earlier CPIS and water-source analyses. |
| `1_analyze_data/` | Supporting/older | CPIS expansion notebooks and motivation figures. |
| `2_water_source_analysis/` | Supporting | CPIS activity, elevation, groundwater, dam-accessibility, anomaly, and spatial-statistics analyses used to interpret outside-command-area irrigation. |
| `Archive/` | Archive | Pointer to archived exploratory material. |
| `utils/` | Shared | Utility functions used by notebooks and scripts. |

## Source Of Truth

For the current paper, start in `paper1_command_area_growth/`.

Final manuscript-facing outputs should trace to:

- `Data/Processed/Paper1_CommandAreaGrowth/final_tables/`
- `Output/Paper1_CommandAreaGrowth/tables/`
- `Output/Paper1_CommandAreaGrowth/figures/`
- `Output/Paper1_CommandAreaGrowth/diagnostics/`

The older notebook folders remain useful context, but they should not override
the script-first Paper 1 workflow.
