# Africa_Irrigation
 Project exploring how much irrigation Center Pivots have accounted for in the context of the expansion of irrigation as a whole in SSA from 2000 to 2021. 

## Instructions

1. Install [Conda](http://conda.io/)


2. Create environment and install requirements

```bash
conda env create -n irrigation -f requirements.yml
conda activate irrigation
```

3. For each Notebook download the required raw data and run the required processing code before running the Notebook itself.

## Content

#### Key:

- **Bold**: Indicates full description of figure or file

- **<ins>Bold Underline</ins>**: Indicates the file is necessary to produce the notebook's results

- [Blue Underline](https://github.com/rellimylime/Africa_Irrigation/blob/main/README.md): Link


### Irrigation vs Center Pivot Expansion

-----

### [0_CPIS_vs_Total](https://github.com/rellimylime/Africa_Irrigation/blob/main/Code/1_analyze_data/0_CPIS_vs_Total.ipynb)

#### Results:

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
  
<details>
  <summary><strong style="font-size:16px;">Raw data required:</strong></summary>
  <br>
  <blockquote>
    <strong>(1)</strong> <a href="https://hub.arcgis.com/datasets/07610d73964e4d39ab62c4245d548625/explore"><code>'Africa_boundaries_shp_path'</code></a>
    <br>
    <strong>(2)</strong> <a href="https://data.apps.fao.org/aquastat/?lang=en&share=f-30f07e71-7f5e-4803-b98b-362511369dd4"><code>'AQUA_World_path'</code></a>
    <br>
    <strong>(3)</strong> <a href="https://github.com/DetectCPIS/global_cpis_shp"><code>'CPIS_2000_shp_path'</code></a> <em>instructions below</em>
    <br>
    <strong>(4)</strong> <a href="https://github.com/DetectCPIS/global_cpis_shp"><code>'CPIS_2021_shp_path'</code></a> <em>instructions below</em>
  </blockquote>
</details>

<details>
  <summary><strong style="font-size:16px;">Required Processing Notebooks:</strong></summary>
  <br>
  <p><a href="https://github.com/rellimylime/Africa_Irrigation/blob/main/Code/0_process_data/0_filter_AQUASTAT.ipynb"><em><strong>0_Filter_AQUASTAT</strong></em></a>: Output:</p>
  <blockquote>
    <p><strong>(a)</strong> <strong><ins><code>'AQUA_AfricaIrrigation'</code></ins></strong>:</p>
    <blockquote>(2)<code>'AQUA_World_path'</code> filtered to Africa</blockquote>
    <p><strong>(b)</strong> <strong><ins><code>'AQUA_SSAIrrigation'</code></ins></strong>:</p>
    <blockquote>(2)<code>'AQUA_World_path'</code> filtered to Sub-Saharan Africa</blockquote>
    <p><strong>(c)</strong> <strong><ins><code>'AQUA_AfricaIrrigation_2000'</code></ins></strong>:</p>
    <blockquote>(a) filtered to the year 2000</blockquote>
    <p><strong>(d)</strong> <strong><ins><code>'AQUA_AfricaIrrigation_2021'</code></ins></strong>:</p>
    <blockquote>(a) filtered to the year 2021</blockquote>
    <p><strong>(e)</strong> <strong><ins><code>'AQUA_SSAIrrigation_2000'</code></ins></strong>:</p>
    <blockquote>(b) filtered to the year 2000</blockquote>
    <p><strong>(f)</strong> <strong><ins><code>'AQUA_SSAIrrigation_2021'</code></ins></strong>:</p>
    <blockquote>(b) filtered to the year 2021</blockquote>
  </blockquote>

  <p><a href="https://github.com/rellimylime/Africa_Irrigation/blob/main/Code/0_process_data/1_CPIS_by_Country.ipynb"><em><strong>1_CPIS_by_Country</strong></em></a>: Output:</p>
  <blockquote>
    <p><strong>(g)</strong> <strong><ins><code>'Africa_CPIS_2000_shp_path'</code></ins></strong>:</p>
    <blockquote>(3) filtered to Africa with geometry area (<code>'Area_m2'</code>) column added</blockquote>
    <p><strong>(h)</strong> <strong><ins><code>'Africa_CPIS_2021_shp_path'</code></ins></strong>:</p>
    <blockquote>(4) filtered to Africa with geometry area (<code>'Area_m2'</code>) column added</blockquote>
  </blockquote>

  <blockquote>
    <p><strong><a href="https://github.com/rellimylime/Africa_Irrigation/blob/main/Output/Process/0_Figure0.png">1_Figure0</a></strong>: Maps of CPIS placement (3,4) layered on Africa boundaries (1) for 2000 and 2021</p>
  </blockquote>
</details>
  
----

### [1_CPIS_Africa_Map](https://github.com/rellimylime/Africa_Irrigation/blob/main/Code/1_analyze_data/1_CPIS_Africa_Map.ipynb)

#### Results:
>**(o)** ```'Comp_by_Country_2000_path'```
> >The area of all irrigation and of CPIS per country and % (CPIS area / total irrigated area) per country in 2000
>
>**(p)** ```'Comp_by_Country_2021_path'```
> >The area of all irrigation and of CPIS per country and % (CPIS area / total irrigated area) per country in 2000
>
>**(q)** ```'CPIS_Area_by_Country_2000_csv_path'```
> >The area of all irrigation and of all CPIS per country and % (CPIS area / total irrigated area) per country in 2000
>
>**(r)** ```'CPIS_Area_by_Country_2000_csv_path'```
> >The area of all irrigation and of CPIS per country and % (CPIS area / total irrigated area) per country in 2021
>
>**![1_Figure1](https://github.com/rellimylime/Africa_Irrigation/blob/main/Output/Analyze/1_Figure1.png)**
> Dual map of Africa comparing percent AEI that is CPIS from 2000 to 2021 with non-SSA and non-arid regions hashed out

<details>
  <summary><strong style="font-size:16px;">Raw Data Required:</strong></summary>
  <br>
  <p><strong>(1)</strong> <a href="https://hub.arcgis.com/datasets/07610d73964e4d39ab62c4245d548625/explore"><code>'Africa_boundaries_shp_path'</code></a></p>
  <p><strong>(2)</strong> <a href="https://data.apps.fao.org/aquastat/?lang=en&share=f-30f07e71-7f5e-4803-b98b-362511369dd4"><code>'AQUA_World_path'</code></a></p>
  <p><strong>(3)</strong> <a href="https://github.com/DetectCPIS/global_cpis_shp"><code>'CPIS_2000_shp_path'</code></a> <em>_instructions below_</em></p>
  <p><strong>(4)</strong> <a href="https://github.com/DetectCPIS/global_cpis_shp"><code>'CPIS_2021_shp_path'</code></a> <em>_instructions below_</em></p>
  <p><strong>(5)</strong> <a href="https://figshare.com/articles/dataset/Global_Aridity_Index_and_Potential_Evapotranspiration_ET0_Climate_Database_v2/7504448"><code>'Global_Aridity_Raster_path'</code></a></p>
</details>

<details>
  <summary><strong style="font-size:16px;">Required Processing Notebooks:</strong></summary>
  <br>
  <p><a href="https://github.com/rellimylime/Africa_Irrigation/blob/main/Code/0_process_data/0_Filter_AQUASTAT.ipynb"><em><strong>0_Filter_AQUASTAT</strong></em></a>: Output:</p>
  <blockquote>
    <p><strong>(a)</strong> <strong><ins><code>'AQUA_AfricaIrrigation'</code></ins></strong>:</p>
    <blockquote>(2) <code>'AQUA_World_path'</code> filtered to Africa</blockquote>
    <p><strong>(b)</strong> <strong><ins><code>'AQUA_SSAIrrigation'</code></ins></strong>:</p>
    <blockquote>(2) <code>'AQUA_World_path'</code> filtered to Sub-Saharan Africa</blockquote>
    <p><strong>(c)</strong> <strong><ins><code>'AQUA_AfricaIrrigation_2000'</code></ins></strong>:</p>
    <blockquote>(a) filtered to the year 2000</blockquote>
    <p><strong>(d)</strong> <strong><ins><code>'AQUA_AfricaIrrigation_2021'</code></ins></strong>:</p>
    <blockquote>(a) filtered to the year 2021</blockquote>
    <p><strong>(e)</strong> <strong><ins><code>'AQUA_SSAIrrigation_2000'</code></ins></strong>:</p>
    <blockquote>(b) filtered to the year 2000</blockquote>
    <p><strong>(f)</strong> <strong><ins><code>'AQUA_SSAIrrigation_2021'</code></ins></strong>:</p>
    <blockquote>(b) filtered to the year 2021</blockquote>
  </blockquote>

  <p><a href="https://github.com/rellimylime/Africa_Irrigation/blob/main/Code/0_process_data/1_CPIS_by_Country.ipynb"><em><strong>1_CPIS_by_Country</strong></em></a>: Output:</p>
  <blockquote>
    <p><strong>(g)</strong> <strong><ins><code>'Africa_CPIS_2000_shp_path'</code></ins></strong>:</p>
    <blockquote>(3) filtered to Africa with geometry area (<code>'Area_m2'</code>) column added</blockquote>
    <p><strong>(h)</strong> <strong><ins><code>'Africa_CPIS_2021_shp_path'</code></ins></strong>:</p>
    <blockquote>(4) filtered to Africa with geometry area (<code>'Area_m2'</code>) column added</blockquote>
    <p><strong><a href="https://github.com/rellimylime/Africa_Irrigation/blob/main/Output/Process/0_Figure0.png">1_Figure0</a></strong>: Maps of CPIS placement (3,4) layered on Africa boundaries (1) for 2000 and 2021</p>
  </blockquote>

  <p><a href="https://github.com/rellimylime/Africa_Irrigation/blob/main/Code/0_process_data/2_Aridity_Refinement.ipynb"><em><strong>2_Aridity_Refinement</strong></em></a>: Output:</p>
  <blockquote>
    <p><strong>(i)</strong> <strong><ins><code>'Africa_Arid_Regions_tif_path'</code></ins></strong>:</p>
    <blockquote>(5) trimmed by Africa bounding box</blockquote>
    <p><strong>(j)</strong> <strong><ins><code>'Africa_Arid_Regions_tif_path2'</code></ins></strong>:</p>
    <blockquote>(i) trimmed by (1)</blockquote>
    <p><strong>(k)</strong> <strong><ins><code>'Africa_All_shp_path'</code></ins></strong>:</p>
    <blockquote>(5) with 1s for all elements &lt; 5000 and 0s otherwise</blockquote>
    <p><strong>(l)</strong> <code>'Africa_Semi_Arid_shp_path'</code>:</p>
    <blockquote>(i) filtered to (2000, 5000)</blockquote>
    <p><strong>(m)</strong> <code>'Africa_Arid_shp_path'</code>:</p>
    <blockquote>(i) filtered to (300, 2000)</blockquote>
    <p><strong>(n)</strong> <code>'Africa_Hyper_Arid_shp_path'</code>:</p>
    <blockquote>(i) filtered to (0, 300)</blockquote>
    <p><a href="https://github.com/rellimylime/Africa_Irrigation/blob/main/Output/Process/2_Figure1.png"><strong>2_Figure1</strong></a>: Figure containing outlines of each of the four aridity layers</p>
  </blockquote>
</details>

-----

### [2_CPIS_by_Region](https://github.com/rellimylime/Africa_Irrigation/blob/main/Code/1_analyze_data/2_CPIS_by_Region.ipynb)
  
#### Results:

>![2_Figure1](https://github.com/rellimylime/Africa_Irrigation/blob/main/Output/Analyze/2_Figure1.png)
> Dual map of Africa comparing percent AEI that is CPIS from 2000 to 2021 with non-SSA and non-arid regions hashed out
  
<details>
  <summary><strong style="font-size:16px;">Raw Data Required:</strong></summary>
  <br>
  <p><strong>(1)</strong> <a href="https://hub.arcgis.com/datasets/07610d73964e4d39ab62c4245d548625/explore"><code>'Africa_boundaries_shp_path'</code></a></p>
  <p><strong>(2)</strong> <a href="https://data.apps.fao.org/aquastat/?lang=en&share=f-30f07e71-7f5e-4803-b98b-362511369dd4"><code>'AQUA_World_path'</code></a></p>
  <p><strong>(3)</strong> <a href="https://github.com/DetectCPIS/global_cpis_shp"><code>'CPIS_2000_shp_path'</code></a> <em>_instructions below_</em></p>
  <p><strong>(4)</strong> <a href="https://github.com/DetectCPIS/global_cpis_shp"><code>'CPIS_2021_shp_path'</code></a> <em>_instructions below_</em></p>
  <p><strong>(5)</strong> <a href="https://figshare.com/articles/dataset/Global_Aridity_Index_and_Potential_Evapotranspiration_ET0_Climate_Database_v2/7504448"><code>'Global_Aridity_Raster_path'</code></a></p>
</details>

<details>
  <summary><strong style="font-size:16px;">Required Notebook:</strong></summary>
  <br>
  <p>Follow instructions for <a href="https://github.com/rellimylime/Africa_Irrigation/blob/main/Code/1_analyze_data/1_CPIS_Africa_Map.ipynb"><em><strong>1_CPIS_Africa_Map</strong></em></a> <em>(above)</em></p>
  <p>Output:</p>
  <blockquote>
    <p><strong>(o)</strong> <code>'Comp_by_Country_2000_path'</code></p>
    <p><strong>(p)</strong> <code>'Comp_by_Country_2021_path'</code></p>
    <p><strong>(q)</strong> <ins><strong><code>'CPIS_Area_by_Country_2000_csv_path'</code></strong></ins></p>
    <p><strong>(r)</strong> <ins><strong><code>'CPIS_Area_by_Country_2021_csv_path'</code></strong></ins></p>
    <p><a href="https://github.com/rellimylime/Africa_Irrigation/blob/main/Output/Analyze/1_Figure1.png"><strong>1_Figure1</strong></a></p>
  </blockquote>
</details>

-----

### [3_Dams_AEI_Targeting_Ratios](https://github.com/rellimylime/Africa_Irrigation/blob/main/Code/1_analyze_data/3_Dams_AEI_Targeting_Ratios.ipynb)

#### Results

>![3_Figure0](https://github.com/rellimylime/Africa_Irrigation/blob/main/Output/Analyze/3_Figure0.png)
> Targeting ratios and distance ranges plotted (over all arid area)  
>
>![3_Figure1](https://github.com/rellimylime/Africa_Irrigation/blob/main/Output/Analyze/3_Figure1.png)
> Targeting ratios and distance ranges plotted (over semi-arid area)
>
>![3_Figure2](https://github.com/rellimylime/Africa_Irrigation/blob/main/Output/Analyze/3_Figure2.png)
> Targeting ratios and distance ranges plotted (over arid area)
>
>![3_Figure3](https://github.com/rellimylime/Africa_Irrigation/blob/main/Output/Analyze/3_Figure3.png)
> Targeting ratios and distance ranges plotted (over hyper-arid area)  

<details>
  <summary><strong style="font-size:16px;">Raw Data Required:</strong></summary>
  <br>
  <p><strong>(1)</strong> <a href="https://hub.arcgis.com/datasets/07610d73964e4d39ab62c4245d548625/explore"><code>'Africa_boundaries_shp_path'</code></a></p>
  <p><strong>(2)</strong> <a href="https://data.apps.fao.org/aquastat/?lang=en&share=f-30f07e71-7f5e-4803-b98b-362511369dd4"><code>'AQUA_World_path'</code></a></p>
  <p><strong>(5)</strong> <a href="https://figshare.com/articles/dataset/Global_Aridity_Index_and_Potential_Evapotranspiration_ET0_Climate_Database_v2/7504448"><code>'Global_Aridity_Raster_path'</code></a></p>
  <p><strong>(6)</strong> <code>'Combined_CPIS_shp_path'</code> Generated using the following code:</p>
  <blockquote>
    <p>- <a href="https://github.com/anna-boser/Africa_corporate_irrigation/blob/main/code/0_process_data/0_subset_CPIS.py">File 1</a></p>
    <p>- <a href="https://github.com/anna-boser/Africa_corporate_irrigation/blob/main/code/0_process_data/1_combine_2000_2021_CPIS.py">File 2</a></p>
  </blockquote>
  <p><strong>(7)</strong> <a href="https://sedac.ciesin.columbia.edu/data/set/grand-v1-dams-rev01/maps?facets=region:africa"><code>'Global_Dam_Data_csv_path'</code></a></p>
  <p><strong>(8)</strong> <a href="https://zenodo.org/records/7809342"><code>'Africa_AEI_2015_asc_path'</code></a></p>
</details>

<details>
  <summary><strong style="font-size:16px;">Required Processing Notebooks:</strong></summary>
  <br>
  
  <p><a href="https://github.com/rellimylime/Africa_Irrigation/blob/main/Code/0_process_data/2_Aridity_Refinement.ipynb"><em><strong>2_Aridity_Refinement</strong></em></a>: Output:</p>
  <blockquote>
    <p><strong>(i)</strong> <strong><ins><code>'Africa_Arid_Regions_tif_path'</code></ins></strong>:</p>
    <blockquote>(5) trimmed by Africa bounding box</blockquote>
    <p><strong>(j)</strong> <strong><ins><code>'Africa_Arid_Regions_tif_path2'</code></ins></strong>:</p>
    <blockquote>(i) trimmed by (1)</blockquote>
    <p><strong>(k)</strong> <strong><ins><code>'Africa_All_shp_path'</code></ins></strong>:</p>
    <blockquote>(5) with 1s for all elements &lt; 5000 and 0s otherwise</blockquote>
    <p><strong>(l)</strong> <code>'Africa_Semi_Arid_shp_path'</code>:</p>
    <blockquote>(i) filtered to (2000, 5000)</blockquote>
    <p><strong>(m)</strong> <code>'Africa_Arid_shp_path'</code>:</p>
    <blockquote>(i) filtered to (300, 2000)</blockquote>
    <p><strong>(n)</strong> <code>'Africa_Hyper_Arid_shp_path'</code>:</p>
    <blockquote>(i) filtered to (0, 300)</blockquote>
    <p><a href="https://github.com/rellimylime/Africa_Irrigation/blob/main/Output/Process/2_Figure1.png"><strong>2_Figure1</strong></a>: Figure containing outlines of each of the four aridity layers</p>
  </blockquote>

  <p><a href="https://github.com/rellimylime/Africa_Irrigation/blob/main/Code/0_process_data/4_CPIS_overlay.ipynb"><em><strong>4_CPIS_Processing</strong></em></a>: Output:</p>
  <blockquote>
    <p><strong>(s)</strong> <strong><ins><code>'Combined_CPIS_Reproj_shp_path'</code></ins></strong>:</p>
    <blockquote>(6) reprojected to EPSG:3857</blockquote>
    <p><strong>(t)</strong> <strong><ins><code>'Combined_CPIS_All_shp_path'</code></ins></strong>:</p>
    <blockquote>(6) filtered to all aridity layers</blockquote>
    <p><strong>(u)</strong> <strong><ins><code>'Combined_CPIS_Semi_Arid_shp_path'</code></ins></strong>:</p>
    <blockquote>(6) filtered to semi-arid areas</blockquote>
    <p><strong>(v)</strong> <strong><ins><code>'Combined_CPIS_Arid_shp_path'</code></ins></strong>:</p>
    <blockquote>(6) filtered to arid areas</blockquote>
    <p><strong>(w)</strong> <strong><ins><code>'Combined_CPIS_Hyper_Arid_shp_path'</code></ins></strong>:</p>
    <blockquote>(6) filtered to hyper-arid areas</blockquote>
  </blockquote>

  <p><a href="https://github.com/rellimylime/Africa_Irrigation/blob/main/Code/0_process_data/5_Dam_processing.ipynb"><em><strong>5_Dam_Processing</strong></em></a>: Output:</p>
  <blockquote>
    <p><strong>(x)</strong> <code>'Africa_Dam_csv_path'</code>:</p>
    <blockquote>(7) filtered to Africa</blockquote>
    <p><strong>(y)</strong> <code>'Africa_Dam_Irrigation_csv_path'</code>:</p>
    <blockquote>(x) filtered to dams which have 'Irrigation' listed as a purpose</blockquote>
    <p><strong>(z)</strong> <code>'Africa_Dam_Irrigation_Only_csv_path'</code>:</p>
    <blockquote>(x) filtered to dams which _only_ have 'Irrigation' listed as a purpose</blockquote>
    <p><strong>(aa)</strong> <strong><ins><code>'Africa_Dam_Semi_Arid_shp_path'</code></ins></strong>:</p>
    <blockquote>(y) filtered to semi-arid area</blockquote>
    <p><strong>(bb)</strong> <strong><ins><code>'Africa_Dam_Arid_shp_path'</code></ins></strong>:</p>
    <blockquote>(y) filtered to arid area</blockquote>
    <p><strong>(cc)</strong> <strong><ins><code>'Africa_Dam_Hyper_Arid_shp_path'</code></ins></strong>:</p>
    <blockquote>(y) filtered to hyper-arid area</blockquote>
    <p><strong>(dd)</strong> <strong><ins><code>'Africa_Dam_Semi_All_shp_path'</code></ins></strong>:</p>
    <blockquote>(y) filtered to all aridity layers</blockquote>
  </blockquote>

  <p><a href="https://github.com/rellimylime/Africa_Irrigation/blob/main/Code/0_process_data/6_AEI_trimming.ipynb"><em><strong>6_AEI_Processing</strong></em></a>: Output:</p>
  <blockquote>
    <p><strong>(ee)</strong> <code>'AEI_2015_cropped_tif_path'</code>:</p>
    <blockquote>(8) cropped to Africa</blockquote>
    <p><strong>(ff)</strong> <code>'AEI_2015_reproj_gpkg_path'</code>:</p>
    <blockquote>(ee) converted to a GDF and re-projected to EPSG:3857</blockquote>
    <p><strong>(gg)</strong> <strong><ins><code>'AEI_2015_Semi_Arid_shp_path'</code></ins></strong>:</p>
    <blockquote>(ff) trimmed to semi-arid area</blockquote>
    <p><strong>(hh)</strong> <strong><ins><code>'AEI_2015_Arid_shp_path'</code></ins></strong>:</p>
    <blockquote>(ff) trimmed to arid area</blockquote>
    <p><strong>(ii)</strong> <strong><ins><code>'AEI_2015_Hyper_Arid_shp_path'</code></ins></strong>:</p>
    <blockquote>(ff) trimmed to hyper-arid area</blockquote>
    <p><strong>(jj)</strong> <strong><ins><code>'AEI_2015_All_shp_path'</code></ins></strong>:</p>
    <blockquote>(ff) trimmed to all aridity layers</blockquote>
  </blockquote>
</details>





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