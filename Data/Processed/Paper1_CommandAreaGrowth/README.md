# Paper 1 Processed Data

Canonical processed artifacts for the command-area growth paper live here.

The main run uses the raw `No_Crop_Vectorized_Command_Area` export as the
command-area source. Initial command-area masks are exploratory/sensitivity
inputs and are not the default source for paper tables.

## Subdirectories

- `yearly_command_areas/`: merged, overlap-free command-area layers by analysis year.
- `extracted_irrigation/`: intermediate inside/outside raster extraction outputs.
- `final_tables/`: stable CSVs used by paper figures, tables, and text.

## Expected final tables

- `data_inventory.csv`
- `inside_outside_irrigation_by_country_year.csv`
- `growth_decomposition_by_country.csv`
- `growth_decomposition_summary.csv`
- `cpis_command_area_supporting_evidence.csv`
