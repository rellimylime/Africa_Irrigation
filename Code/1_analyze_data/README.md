# 1_analyze_data

Expansion analysis notebooks that quantify how CPIS growth compares to total irrigation growth across Africa and Sub-Saharan Africa from 2000 to 2021. These notebooks answer the "how fast and where" question before the water source notebooks ask "why."

Run `Code/0_process_data` notebooks first.

---

## 0_CPIS_vs_Total.ipynb

**What it does:** Combines CPIS polygon areas with AQUASTAT total irrigation figures to compute growth rates and CPIS share of irrigation for Africa and SSA at the continental level.

**Why it's necessary:** This notebook produces the headline finding that anchors the entire project: CPIS expanded 191% in SSA while total irrigated area grew only 94.6%, meaning CPIS is structurally outpacing general irrigation development.

**Key results:**
- Africa: total irrigation +51.6%, CPIS +191.2% (share: 2.85% → 5.48%)
- SSA: total irrigation +94.6%, CPIS +191.2% (share: 6.81% → 10.19%)
- CPIS area in SSA: 308,000 ha (2000) → 897,000 ha (2021)

**Outputs:**
- `Output/Analyze/0_Figure1.png` — Africa CPIS vs total irrigation trend lines (2000–2021)
- `Output/Analyze/0_Figure2.png` — SSA CPIS vs total irrigation trend lines (2000–2021)
- `Output/Analyze/0_Figure3.png` — SSA vs non-SSA comparison

---

## 1_CPIS_Africa_Map.ipynb

**What it does:** Computes CPIS as a percentage of total irrigated area for each country and maps the result for 2000 and 2021 side by side.

**Why it's necessary:** The continental trend (notebook 0) masks enormous country-level variation. This map shows that CPIS uptake is concentrated in southern Africa and reveals outliers like Namibia and Botswana where CPIS already dominates irrigated agriculture.

**Key results:**
- Namibia: CPIS exceeds reported AEI by 2021 (data boundary issue, noted in notebook)
- Botswana: 80% of irrigated area is CPIS by 2021
- Southern Africa dominates; Northern Africa has essentially zero CPIS

**Outputs:**
- `CPIS_Area_SSA_by_Country_2000.csv`, `_2021.csv` — CPIS area per country
- `Comp_by_Country_2000.csv`, `Comp_by_Country_2021.csv` — CPIS % of irrigation per country
- `Output/Analyze/1_Figure1.png` — dual-panel choropleth map (2000 left, 2021 right), arid regions outlined, non-SSA hatched

---

## 2_CPIS_by_Region.ipynb

**What it does:** Disaggregates the continental CPIS and irrigation figures into four regions (Northern, Southern, Eastern, Western Africa) and plots growth side by side for 2000 and 2021.

**Why it's necessary:** The continental result is dominated by Southern Africa's large CPIS base. This notebook shows that East and West Africa have the fastest growth rates (283% and 246% respectively), pointing to where rapid and potentially under-resourced expansion is occurring.

**Key results:**

| Region | CPIS growth | Total irrig. growth | CPIS share 2021 |
|--------|-------------|---------------------|-----------------|
| East Africa | +283% | +79% | 6.5% |
| West Africa | +246% | +26% | 3.1% |
| Southern Africa | +191% | +50% | 14.4% |
| Central Africa | +47% | +2% | 0.2% |
| Northern Africa | 0% | +50% | 0% |

**Outputs:**
- `Output/Analyze/2_Figure1.png` — 2×2 regional bar charts, 2000 vs 2021, CPIS share annotated

---

## 3_Dams_AEI_Targeting_Ratios.ipynb

> **Archived.** Superseded by `Code/2_water_source_analysis/5_spatial_statistics.ipynb`.

---

## 4_Dam_Growth_Context.ipynb

**What it does:** Tracks dam count in arid SSA from 2000 to 2021 at the country level and maps where new dams were built.

**Why it's necessary:** Establishes that dam infrastructure grew only ~3% (2,674 → 2,763 dams, net +89) over the same period that CPIS grew 191%. This asymmetry is the primary empirical motivation for asking whether CPIS are actually using dam water — and for the elevation-based analysis that follows.

**Key results:**
- Total dams in arid SSA: 2,674 (2000) → 2,763 (2021), +3.3%
- South Africa largest absolute growth (+37 dams); Eritrea highest % growth (+400%, from 1 to 5)
- Most countries: zero new dams over 21 years

**Outputs:**
- Figure: dam locations 2000 vs 2021 (red vs blue points on arid SSA boundaries)
- Figure: choropleth of dam count by country, 2000 and 2021, with change panel (log-scaled YlGn colormap)
- Figure: new dams only (green points), constructed 2000–2021
