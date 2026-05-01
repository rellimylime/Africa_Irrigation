# Code

This folder contains all Jupyter notebooks used to prepare, analyze, and interpret data for the Africa_Irrigation project.

Each subfolder has its own README with more detailed instructions, inputs, and outputs. The main subfolders are:

- **paper1_command_area_growth/**
  Canonical workflow for the paper asking whether irrigation expansion in arid Sub-Saharan Africa occurred inside or outside modeled large-dam command areas. Final paper figures and tables should trace back to this folder.

- **0_process_data/**
  Contains notebooks that download, filter, and preprocess raw datasets. Outputs from these notebooks are stored in `Data/Processed` and `Output/Process`. These outputs are required inputs for all subsequent analysis notebooks.

- **1_analyze_data/**
  Contains notebooks that examine the expansion of center pivot irrigation systems (CPIS) compared to total irrigation in Africa and Sub-Saharan Africa from 2000 to 2021. Analyses include continental trends, country-level comparisons, and regional (aridity/SSA) breakdowns. Outputs are stored in `Output/Analyze`.

- **2_water_source_analysis/**
  Supporting evidence for interpreting outside-command-area irrigation and CPIS water-source plausibility. Analyses include elevation-based dam accessibility, NDWI activity classification, Gaussian process groundwater interpolation, anomaly detection, and spatial statistics.

- **Archive/**
  Pointer folder. The old command-area archive notebooks were moved to `paper1_command_area_growth/legacy_notebooks/` so they remain available as paper references.

For dataset locations and descriptions, see the `config.yaml` file at the root of the repository.
