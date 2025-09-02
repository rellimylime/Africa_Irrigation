# Africa_Irrigation

Project assessing how much of irrigation expansion in Africa, and in Sub-Saharan Africa (SSA), is attributable to center pivot irrigation systems (CPIS) from 2000 to 2021. The work also examines relationships with dams and groundwater.

## Repository structure

```txt
Africa_Irrigation/
│
├── Code/
│   ├── 0_process_data/    (download, filter, preprocess datasets)
│   ├── 1_analyze_data/    (CPIS expansion and irrigation trend analyses)
│   └── 2_dam_analysis/    (dam and groundwater related analyses)
│
├── Data/
│   ├── Raw/               (external inputs, unmodified)
│   └── Processed/         (intermediate and final processed artifacts)
│
├── Output/
│   ├── Process/           (figures and tables from preprocessing)
│   └── Analyze/           (figures and tables from analyses)
│
├── config.yaml            (all dataset locations and brief descriptions)
└── README.md              (this file)
```
Each folder has its own README with inputs, outputs, and run notes. The exact locations of datasets used in any notebook are specified in config.yaml.


## Setup
1. Install Conda

2. Create the environment and install requirements:

Copy code:
```bash
conda env create -n irrigation -f requirements.yml
conda activate irrigation
```
## Quick start
1. Set paths in config.yaml to your local copies of the required datasets.

2. Run the preprocessing notebooks in Code/0_process_data as needed for your analysis of interest.

3. Run the analysis notebooks in Code/1_analyze_data or Code/2_dam_analysis.

4. See outputs under Output/Process and Output/Analyze.

Detailed, step-by-step instructions are in the sub-READMEs inside each code folder.

## Key analyses and results
This section summarizes headline findings and points to the main notebooks and representative figures. Full details, intermediate files, and all figure variants are in the sub-READMEs.

### A. Irrigation vs CPIS expansion (2000 to 2021)
Notebook: [Code/1_analyze_data/0_CPIS_vs_Total.ipynb](Code/1_analyze_data/0_CPIS_vs_Total.ipynb)

Representative figures:

- [Output/Analyze/0_Figure1.png](Output/Analyze/0_Figure1.png) (Africa)

- [Output/Analyze/0_Figure2.png](Output/Analyze/0_Figure2.png) (SSA)

- [Output/Analyze/0_Figure3.png](Output/Analyze/0_Figure3.png) (combined axes)

Results at a glance:

- Africa, area equipped for irrigation increased by about 51.6%. CPIS area increased by about 148.9%.

- SSA, area equipped for irrigation increased by about 94.6%. CPIS area increased by about 191.2%.

- CPIS share of irrigated area increased (Africa: ~3.6% → ~6.0%, SSA: ~6.8% → ~10.2%).

### B. Country and regional distribution
Notebook: [Code/1_analyze_data/1_CPIS_Africa_Map.ipynb](Code/1_analyze_data/1_CPIS_Africa_Map.ipynb)

Related notebook: [Code/1_analyze_data/2_CPIS_by_Region.ipynb](Code/1_analyze_data/2_CPIS_by_Region.ipynb)

Representative figure: [Output/Analyze/1_Figure1.png](Output/Analyze/1_Figure1.png)

What it shows:

- Country-level maps for 2000 and 2021, CPIS percent of total area equipped for irrigation.

- Views masked to SSA and aridity zones to highlight spatial patterns.

Key outputs:

- Country comparison tables for 2000 and 2021, including CPIS area, total irrigated area, and CPIS percent.

### C. Dam and groundwater analysis
Folder: [Code/2_dam_analysis](Code/2_dam_analysis)

Notebooks:

- Dams and proximity targeting ratios: [Code/2_dam_analysis/3_Dams_AEI_Targeting_Ratios.ipynb](Code/2_dam_analysis/3_Dams_AEI_Targeting_Ratios.ipynb)

Figures: [Output/Analyze/3_Figure0.png](Output/Analyze/3_Figure0.png) to [Output/Analyze/3_Figure3.png](Output/Analyze/3_Figure3.png)

- Groundwater productivity and CPIS: [Code/2_dam_analysis/4_Groundwater.ipynb](Code/2_dam_analysis/4_Groundwater.ipynb)

Figure: [Output/Analyze/4_Figure1.png](Output/Analyze/4_Figure1.png)

What it tests:

- Whether CPIS siting is concentrated near dams within aridity zones, using targeting ratios by distance bands.

- Whether CPIS is associated with mapped groundwater productivity classes.

Headline takeaways (see sub-READMEs for details):

- Dams explain part of the spatial pattern, but not all CPIS expansion.

- Groundwater productivity appears correlated with CPIS locations in several aridity classes.

- Confidence intervals and sensitivity checks are reported in the figures and tables.

### Data sources (primary)
Citations and links for the main external datasets. All paths are configured in [config.yaml](config.yaml). 

Preprocessing steps are documented in the [Code/0_process_data](Code/0_process_data) sub-README.

- CPIS shapefiles, 2000 and 2021, DetectCPIS project (see repository for download instructions).

- AQUASTAT dissemination system tables (Africa and SSA subsets, selected years between 2000 and 2021).

- GRanD dams database (Africa subset).

- Global Aridity Index and PET v2 (aridity classes and masks).

- Area Equipped for Irrigation rasters, 2000 and 2015, including MEIER products where used.

- Groundwater productivity maps for Africa.

Notes:

- Some countries or territories are not present in AQUASTAT for the selected extracts (see config.yaml and the process README for handling choices).

- All derived products are written to Data/Processed and Output/Process.

### Reproducibility
- Pin the environment with requirements.yml.

- Keep config.yaml as the single source of truth for data paths and dataset descriptions.

- Each notebook reads only from paths defined in config.yaml and from artifacts produced by the process notebooks.

### References
- MacDonald, A. M., Bonsor, H. C., Ó Dochartaigh, B. E., Taylor, R. G. 2012. Quantitative maps of groundwater resources in Africa. Environmental Research Letters 7, 024009.

- Ramankutty, N., Evan, A. T., Monfreda, C., Foley, J. A. 2010. Global Agricultural Lands: Croplands, 2000. NASA SEDAC. https://doi.org/10.7927/H4C8276G

- Additional citations and dataset DOIs are listed in the sub-READMEs and [config.yaml](config.yaml).