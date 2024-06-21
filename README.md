# Africa_Irrigation
 Project exploring how much irrigation Center Pivots have accounted for in the context of the expansion of irrigation as a whole in SSA from 2000 to 2021. 







## Instructions

1. Install [Conda](http://conda.io/)

2. Create environment and install requirements

```bash
conda env create -f requirements.yml
conda activate irrigation
```

3. Add data

### Shapefile containing Center Pivots across the World

You can obtain the shp file containing the world's center pivots [here](https://github.com/DetectCPIS/global_cpis_shp). 

To extract the Center Pivots identified in 2021, download all files in [this folder](https://github.com/DetectCPIS/global_cpis_shp/tree/main/World_CPIS_2021) and run the following code in the terminal: 

```{bash}
cd ~/Downloads 
zip -s 0 World_CPIS_2021.zip --out World_CPIS_2021_together.zip
unzip World_CPIS_2021_together.zip
```
The data from 2000 can be obtained analogously.

### AQUASTAT Dissemination System.csv

Retrieved from https://data.apps.fao.org/aquastat/?lang=en on 06/20/24 using parameters:

- Variables: Environment, Irrigation and drainage development, Water resources, Water use 
- Area: World
- Year: 2021, 2020, 2019, 2015, 2010, 2005, 2000

### Other data

All data is either created using the code in this repository or can be downloaded elsewhere. Refer to the `config.yaml` file for links to and descriptions of datasets.  

#### Some numbers

Unit: 1000 ha (10 km2)

Total Area Equipt for Irrigation in 2000: 10,548.11 ha
Total Area Covered by Central Pivot Irrigation in 2000: 389.43 ha

Total Area Equipt for Irrigation 2020: 15,762.89 ha
Total Area Covered by Central Pivot Irrigation in 2021: 969.19 ha

Percent of Irrigation that CPIS accounted for in:
2000 - 3.69%
2020* - 6.14%

*CPIS data used was from 2021 whereas irrigation data was from 2020, see `config.yaml` for further details on data sources