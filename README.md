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

**Note**: Two adjustments have been made to the original data for efficiency of code; Congo is now known as The Republic of Congo and "Côte d'Ivoire" has been replaced with "CÃ´te d'Ivoire" (both to ensure agreement with country names within the African Boundaries Shapefile).

The following countries were not included in the AQUASTAT data:
French Southern Territories
Mayotte
Reunion
Swaziland 
Western Sahara

### Other data

All data is either created using the code in this repository or can be downloaded elsewhere. Refer to the `config.yaml` file for links to and descriptions of datasets.  

##### Some References

**1. Groundwater Productivity Data**: MacDonald, A M, Bonsor, H C, Ó Dochartaigh, B E, Taylor, R G.  2012.  Quantitative maps of groundwater resources in Africa.  Environmental Research Letters 7, 024009.

**2. Cropland Data**: Ramankutty, N., A.T. Evan, C. Monfreda, and J.A. Foley. 2010. Global Agricultural Lands: Croplands, 2000. Palisades, New York: NASA Socioeconomic Data and Applications Center (SEDAC). https://doi.org/10.7927/H4C8276G. Accessed: 03 July, 2024.