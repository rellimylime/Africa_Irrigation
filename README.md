# Africa Irrigation

This repository contains code, documentation, and selected outputs for remote
sensing analyses of irrigation expansion and water-source context in Africa,
with a current paper workflow focused on arid Sub-Saharan Africa.

The main active paper workflow is:

`Code/paper1_command_area_growth/`

That folder has its own paper-centered README with the research question,
headline results, caveats, run order, and manuscript output guide.

## Where To Start

| Need | Start here |
| --- | --- |
| Understand or run the current paper workflow | `Code/paper1_command_area_growth/README.md` |
| See exact Paper 1 run commands | `Code/paper1_command_area_growth/RUNBOOK.md` |
| Check the command-area source and assumptions | `Code/paper1_command_area_growth/COMMAND_AREA_SOURCE.md` |
| Find Paper 1 figures, tables, and diagnostics | `Output/Paper1_CommandAreaGrowth/README.md` |
| Inspect supporting CPIS and water-source analyses | `Code/2_water_source_analysis/README.md` |
| Check configured input/output paths | `config.yaml` |

## Repository Layout

```txt
Africa_Irrigation/
|-- Code/
|   |-- paper1_command_area_growth/  current Paper 1 workflow
|   |-- 0_process_data/              preprocessing notebooks and scripts
|   |-- 1_analyze_data/              CPIS expansion analyses
|   |-- 2_water_source_analysis/     supporting water-source analyses
|   |-- Archive/                     archived exploratory material
|   `-- utils/                       shared helpers
|-- Data/
|   |-- Raw/                         external inputs, not tracked
|   `-- Processed/                   derived analytical inputs, mostly not tracked
|-- Output/
|   |-- Paper1_CommandAreaGrowth/    selected Paper 1 manuscript assets
|   |-- Archive/                     preserved legacy/generated outputs
|   |-- Analyze/                     older analysis outputs
|   `-- Process/                     older preprocessing outputs
|-- config.yaml                      dataset paths and output locations
`-- requirements.yml                 conda environment specification
```

## Current Paper Workflow

The active paper workflow is script-first. From the repository root:

```bash
bash Code/paper1_command_area_growth/run_paper1_pipeline.sh
```

On Windows PowerShell:

```powershell
.\Code\paper1_command_area_growth\run_paper1_pipeline.ps1
```

The wrapper runs numbered scripts `00` through `07`. Each script writes stable
tables, figures, diagnostics, or intermediate data documented in the Paper 1
runbook.

## Supporting Workflows

The older CPIS and water-source notebooks remain in the repository because they
provide context for interpreting irrigation expansion:

- `Code/0_process_data/` prepares shared inputs.
- `Code/1_analyze_data/` summarizes CPIS expansion and regional patterns.
- `Code/2_water_source_analysis/` explores CPIS activity, elevation feasibility,
  groundwater productivity, dam-accessibility classes, anomaly checks, and
  spatial statistics.

These supporting analyses are useful context, but the current manuscript-facing
inside/outside command-area results are generated from
`Code/paper1_command_area_growth/`.

## Outputs

Selected Paper 1 manuscript assets are tracked under:

`Output/Paper1_CommandAreaGrowth/`

Legacy generated dam-analysis outputs that used to live under `Code/` are
preserved under:

`Output/Archive/Dam_Analysis/`

Large raw data and most intermediate processed data are not tracked. Paths are
configured in `config.yaml`.

## Environment

Create the project environment from:

```bash
conda env create -n irrigation -f requirements.yml
conda activate irrigation
```

Some local runs may need a GIS-enabled Python environment for geospatial
packages such as GeoPandas, Rasterio, Fiona, and Shapely.

## Documentation Notes

- Use `config.yaml` as the path index.
- Use the README inside each workflow directory for purpose, inputs, outputs,
  and run notes.
- Keep generated outputs under `Output/`, not inside `Code/`.
- Treat legacy notebooks as provenance unless their logic has been ported into a
  current workflow or regenerated as a stable table/figure.
