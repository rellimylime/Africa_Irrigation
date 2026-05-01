# Canonical Notebooks

This directory is reserved for the cleaned, paper-facing notebook layer. The
canonical geospatial computations now live one folder up as scripts:

- `../01_prepare_yearly_command_areas.py`
- `../02_extract_irrigation_inside_outside.py`
- `../03_growth_decomposition.py`
- `../00_prepare_paper_inputs.py`

Notebooks here should call or read outputs from those scripts rather than
reimplementing hidden analysis logic.

## Planned notebooks

- `00_data_inventory.ipynb` - implemented; checks configured inputs/outputs and writes inventory CSVs.
- `01_prepare_yearly_command_areas.ipynb` - optional wrapper around the script.
- `02_extract_irrigation_inside_outside.ipynb` - optional wrapper around the script.
- `03_growth_decomposition.ipynb` - optional wrapper around the script.
- `04_country_robustness.ipynb`
- `05_cpis_supporting_evidence.ipynb`
- `06_paper_figures_tables.ipynb`

## Rule of thumb

If a result appears in the paper, it should be generated here or read from a table generated here.
