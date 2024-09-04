# Africa_Irrigation
 Project exploring how much irrigation Center Pivots have accounted for in the context of the expansion of irrigation as a whole in SSA from 2000 to 2021. 

## Content
Key:

- **Bold**: Indicates full description of figure or file

- **<ins>Bold Underline</ins>**: Indicates the file is necessary to produce the notebook's results

- [Blue Underline](https://github.com/rellimylime/Africa_Irrigation/blob/main/README.md): Link


### Irrigation vs Center Pivot Expansion

### [0_CPIS_vs_Total](https://github.com/rellimylime/Africa_Irrigation/blob/main/Code/1_analyze_data/0_CPIS_vs_Total.ipynb)

  

Raw data used:

>**(1)** [```'Africa_boundaries_shp_path'```](https://hub.arcgis.com/datasets/07610d73964e4d39ab62c4245d548625/explore)

>**(2)** [```'AQUA_World_path'```](https://data.apps.fao.org/aquastat/?lang=en&share=f-30f07e71-7f5e-4803-b98b-362511369dd4)

>**(3)** [```'CPIS_2000_shp_path'```](https://github.com/DetectCPIS/global_cpis_shp) _instructions below_

>**(4)** [```'CPIS_2021_shp_path'```](https://github.com/DetectCPIS/global_cpis_shp) _instructions below_

  

Required Processing Notebooks:

[_**0_filter_AQUASTAT**_](https://github.com/rellimylime/Africa_Irrigation/blob/main/Code/0_process_data/0_filter_AQUASTAT.ipynb):
Output:

>**(a)**  **<ins>```'AQUA_AfricaIrrigation'```</ins>**:

> >```'AQUA_World_path'``` filtered to Africa

>**(b)**  **<ins>```'AQUA_SSAIrrigation'```</ins>**:

> >```'AQUA_World_path'``` filtered to Sub-Saharan Africa

>**( c)**  **<ins>```'AQUA_AfricaIrrigation_2000'```**:

> >(a) filtered to the year 2000

>**(d)**  **<ins>```'AQUA_AfricaIrrigation_2021'```**:

> >(a) filtered to the year 2021

>**(e)**  **<ins>```'AQUA_SSAIrrigation_2000'```**:

> >(b) filtered to the year 2000

>**(f)**  **<ins>```'AQUA_SSAIrrigation_2021'```**:

> >(b) filtered to the year 2021

[_**1_CPIS_by_country**_](https://github.com/rellimylime/Africa_Irrigation/blob/main/Code/0_process_data/1_CPIS_by_country.ipynb):
Output:

>**(g)** **<ins>```'Africa_CPIS_2000_shp_path'```</ins>**:

> >(3) filtered to Africa with geometry area (```'Area_m2'```) column added

>**(h)** **<ins>```'Africa_CPIS_2021_shp_path'```</ins>**:

> >(4) filtered to Africa with geometry area (```'Area_m2'```) column added

>[**1_Figure0**](https://github.com/rellimylime/Africa_Irrigation/blob/main/Output/Process/0_Figure0.png):
Maps of CPIS placement (3,4) layered on Africa boundaries (1) for 2000 and 2021

  

Results:

>**![0_Figure1](https://github.com/rellimylime/Africa_Irrigation/blob/main/Output/Analyze/0_Figure1.png)**:
Compares growth of irrigation over all of Africa with CPIS growth

>**![0_Figure2](https://github.com/rellimylime/Africa_Irrigation/blob/main/Output/Analyze/0_Figure2.png)**
Compares growth of irrigation over Sub-Saharan Africa with CPIS growth

>**![0_Figure3](https://github.com/rellimylime/Africa_Irrigation/blob/main/Output/Analyze/0_Figure3.png)**
Figure1 and Figure2 on the same axis

>[15]
>- The area equipped for irrigation in all of Africa increased by 51.56% between 2000 and 2021.
>- The area covered by CPIS in all of Africa increased by 148.89% between 2000 and 2021.
>- In 2000, center pivot irrigation systems made up 3.62% of the total area equipped with irrigation in all of Africa.
>- In 2021, center pivot irrigation systems made up 5.95% of the total area equipped with irrigation in all of Africa."
  
[16]
>- The area equipped for irrigation in Sub-Saharan Africa increased by 94.60% between 2000 and 2021.
>- The area covered by CPIS in Sub-Saharan Africa increased by 191.16% between 2000 and 2021.
>- In 2000, center pivot irrigation systems made up 6.81% of the total area equipped with irrigation in Sub-Saharan Africa.
>- In 2021, center pivot irrigation systems made up 10.19% of the total area equipped with irrigation in Sub-Saharan Africa."

### [1_CPIS_Africa_Map](https://github.com/rellimylime/Africa_Irrigation/blob/main/Code/1_analyze_data/1_CPIS_Africa_Map.ipynb)

  

Raw data required:

>(1) [```'Africa_boundaries_shp_path'```](https://hub.arcgis.com/datasets/07610d73964e4d39ab62c4245d548625/explore)

>(2) [```'AQUA_World_path'```](https://data.apps.fao.org/aquastat/?lang=en&share=f-30f07e71-7f5e-4803-b98b-362511369dd4)

>(3) [```'CPIS_2000_shp_path'```](https://github.com/DetectCPIS/global_cpis_shp) _instructions below_

>(4) [```'CPIS_2021_shp_path'```](https://github.com/DetectCPIS/global_cpis_shp) _instructions below_

>**(5)** [```'Global_Aridity_Raster_path'```](https://figshare.com/articles/dataset/Global_Aridity_Index_and_Potential_Evapotranspiration_ET0_Climate_Database_v2/7504448)
  

Required Processing Notebooks:
[_**0_filter_AQUASTAT**_](https://github.com/rellimylime/Africa_Irrigation/blob/main/Code/0_process_data/0_filter_AQUASTAT.ipynb):
Output:

>(a)  ```'AQUA_AfricaIrrigation'```:

>(b)  ```'AQUA_SSAIrrigation'```:

>( c)  <ins>**```'AQUA_AfricaIrrigation_2000'```**

>(d)  <ins>**```'AQUA_AfricaIrrigation_2021'```**

>(e)  ```'AQUA_SSAIrrigation_2000'```

>(f) ```'AQUA_SSAIrrigation_2021'```


[_**1_CPIS_by_country**_](https://github.com/rellimylime/Africa_Irrigation/blob/main/Code/0_process_data/1_CPIS_by_country.ipynb):
Output:

>**(g)** <ins>**```'Africa_CPIS_2000_shp_path'```**

>**(h)** <ins>**```'Africa_CPIS_2021_shp_path'```**

> [1_Figure0](https://github.com/rellimylime/Africa_Irrigation/blob/main/Output/Process/0_Figure0.png)

[_**2_Aridity_refinement**_](https://github.com/rellimylime/Africa_Irrigation/blob/main/Code/0_process_data/2_Aridity_refinement.ipynb):
Output:
>**(i)** <ins>**```'Africa_Arid_Regions_tif_path'```**
> > (5) trimmed by Africa bounding box
> 
>**(j)** <ins> **```'Africa_Arid_Regions_tif_path2'```**
> >  (i) trimmed by (1)
> 
>**(k)** <ins>**```'Africa_All_shp_path'```**
> > (5) with 1s for all elements < 5000 and 0s otherwise

>**(l)** ```'Africa_Semi_Arid_shp_path'```
> > (i) filtered to (2000, 5000)
>
>**(m)** ```'Africa_Arid_shp_path'```
> > (i) filtered to (300, 2000)
> 
>**(n)** ```'Africa_Hyper_Arid_shp_path'```
> > (i) filtered to (0, 300)

>[**2_Figure1**](https://github.com/rellimylime/Africa_Irrigation/blob/main/Output/Process/2_Figure1.png)
Figure containing outlines of each of the four aridity layers

Results:
>**(o)** ```'Comp_by_Country_2000_csv_path'```
>The area of all irrigation and of all CPIS per country and % (CPIS area / total irrigated area) per country in 2000
>**(p)** ```'Comp_by_Country_2021_csv_path'```
>The area of all irrigation and of CPIS per country and % (CPIS area / total irrigated area) per country in 2000

>**![1_Figure1](https://github.com/rellimylime/Africa_Irrigation/blob/main/Output/Analyze/1_Figure1.png)**
> Dual map of Africa comparing percent AEI that is CPIS from 2000 to 2021 with non-SSA and non-arid regions hashed out
  
  
  
  
  
  
  

-irrigation vs cp expantion

-dam targeting ratios

-gw targeting ratios

  
  

-irrigation vs cp expantion
-dam targeting ratios
-gw targeting ratios


## Instructions

1. Install [Conda](http://conda.io/)

2. Create environment and install requirements

```bash
conda env create -n irrigation -f requirements.yml
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