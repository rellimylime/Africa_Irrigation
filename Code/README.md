# Code

This folder contains all Jupyter notebooks used to prepare, analyze, and interpret data for the Africa_Irrigation project.

Each subfolder has its own README with more detailed instructions, inputs, and outputs. The three main subfolders are:

- **0_process_data/**  
  Contains notebooks that download, filter, and preprocess raw datasets. Outputs from these notebooks are stored in `Data/Processed` and `Output/Process`. These outputs are required inputs for all subsequent analysis notebooks.

- **1_analyze_data/**  
  Contains notebooks that examine the expansion of center pivot irrigation systems (CPIS) compared to total irrigation in Africa and Sub-Saharan Africa from 2000 to 2021. Analyses include continental trends, country-level comparisons, and regional (aridity/SSA) breakdowns. Outputs are stored in `Output/Analyze`.

- **2_dam_analysis/**  
  Contains notebooks focused on the relationship between irrigation expansion, CPIS siting, and water sources (dams and groundwater). Analyses include targeting ratios near dams, aridity zone breakdowns, and groundwater productivity comparisons. Outputs are stored in `Output/Analyze`.

For dataset locations and descriptions, see the `config.yaml` file at the root of the repository.
