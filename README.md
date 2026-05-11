# Africa Irrigation

This repository supports a paper on whether recent irrigation expansion in arid
Sub-Saharan Africa occurred inside modeled large-dam command-area envelopes or
outside them.

The primary paper workflow is script-first and lives in:

`Code/paper1_command_area_growth/`

Compiled manuscript tables, figures, and diagnostics are written to:

`Output/Paper1_CommandAreaGrowth/`

## Current Paper Result

For 2000-2015, total area equipped for irrigation (AEI) grows by about
533,000 ha in arid Sub-Saharan Africa. About 11,900 ha of that growth occurs
inside the modeled large-dam command-area envelopes, and about 521,500 ha occurs
outside them.

The headline result is therefore:

> 97.8% of 2000-2015 AEI growth occurs outside modeled large-dam
> command-area envelopes.

This should not be framed as a claim about true observed service boundaries or
about every possible dam, diversion, canal, farm pond, or groundwater system.
The measured claim is about AEI growth relative to the modeled large-dam
command-area layer used in this repository.

## Where To Start

| Need | Start here |
| --- | --- |
| Run or inspect the main paper workflow | `Code/paper1_command_area_growth/README.md` |
| See exact run commands and outputs | `Code/paper1_command_area_growth/RUNBOOK.md` |
| Understand the command-area source | `Code/paper1_command_area_growth/COMMAND_AREA_SOURCE.md` |
| Find manuscript-ready outputs | `Output/Paper1_CommandAreaGrowth/README.md` |
| Inspect supporting CPIS/water-source analyses | `Code/2_water_source_analysis/README.md` |
| Check dataset paths | `config.yaml` |

## Repository Layout

```txt
Africa_Irrigation/
|-- Code/
|   |-- paper1_command_area_growth/  primary Paper 1 workflow
|   |-- 0_process_data/              older/raw preprocessing notebooks
|   |-- 1_analyze_data/              CPIS expansion notebooks
|   |-- 2_water_source_analysis/     supporting CPIS water-source analyses
|   |-- Archive/                     archived exploratory material
|   `-- utils/                       shared helpers
|-- Data/
|   |-- Raw/                         external inputs
|   `-- Processed/                   derived analytical inputs
|-- Output/
|   |-- Paper1_CommandAreaGrowth/    manuscript-ready Paper 1 assets
|   |-- Archive/                     preserved legacy/generated outputs
|   |-- Analyze/                     older CPIS analysis outputs
|   `-- Process/                     older preprocessing outputs
|-- config.yaml                      dataset paths and output locations
`-- requirements.yml                 conda environment specification
```

## Primary Workflow

Run the full Paper 1 pipeline from the repository root:

```bash
bash Code/paper1_command_area_growth/run_paper1_pipeline.sh
```

On Windows PowerShell:

```powershell
.\Code\paper1_command_area_growth\run_paper1_pipeline.ps1
```

The wrapper runs steps `00` through `07` in order. Each script has a short
module docstring explaining its role, and the paper runbook lists the outputs
written by each stage.

## Documentation Rules

- `config.yaml` is the source of truth for local paths.
- Paper claims should trace to `Code/paper1_command_area_growth/` and
  `Output/Paper1_CommandAreaGrowth/`.
- `Code/2_water_source_analysis/` is supporting evidence for interpretation,
  not the primary measured outcome.
- Legacy notebooks are retained for provenance; do not cite a legacy result
  unless it has been ported into the script-first paper workflow or regenerated
  as a stable table/figure.

## Recommended Language

Use:

> modeled large-dam command-area envelopes

Avoid:

> true command areas

Avoid:

> proof of groundwater irrigation

The outside-command-area result means that observed AEI growth is not explained
by the modeled large-dam command-area layer. Groundwater, CPIS activity, DEM
accessibility, and flow-connectivity analyses help interpret that outside growth.
