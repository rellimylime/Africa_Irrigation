"""
reservoirs_without_dams.py
--------------------------
Counts GDW reservoirs in Africa that have no corresponding dam barrier in the
GDW barriers dataset. Uses GDW_ID as the linking key between the two layers.

Data sources (GDW v1.0):
  - GDW_reservoirs_v1_0.shp : reservoir polygons (one per reservoir)
  - GDW_barriers_v1_0.shp   : dam/barrier point structures (can be >1 per
                               reservoir for MULTI_DAMS cases)
  - Africa_Continent.shp    : Africa boundary for spatial clipping

Results:
  Of 3,615 GDW reservoirs in Africa, only 1 (in Algeria) lacks a corresponding
  barrier entry — effectively 100% of African GDW reservoirs have a dam.

Run with: python Code/Archive/reservoirs_without_dams.py
(from the Africa_Irrigation project root)
"""

import os
import sys
import geopandas as gpd
import pandas as pd

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from Code.utils.utility import load_config, resolve_path

config = load_config()

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
print("Loading GDW reservoir polygons...")
res_path = resolve_path(config['GDW_barrier_shp_path']).replace(
    'GDW_barriers_v1_0.shp', 'GDW_reservoirs_v1_0.shp'
)
gdf_res = gpd.read_file(res_path)
print(f"  {len(gdf_res):,} reservoirs globally")

print("Loading GDW barrier points...")
bar_path = resolve_path(config['GDW_barrier_shp_path'])
gdf_bar = gpd.read_file(bar_path)
print(f"  {len(gdf_bar):,} barriers globally")

print("Loading Africa boundary...")
africa_path = resolve_path(config['Africa_Continent_shp_path'])
gdf_africa = gpd.read_file(africa_path).to_crs(gdf_res.crs)

# ---------------------------------------------------------------------------
# Clip to Africa
# Reservoirs are polygons — use centroids projected to equal-area CRS to
# avoid the geographic-CRS centroid warning.
# Barriers are already points — spatial join directly.
# ---------------------------------------------------------------------------
EQUAL_AREA_CRS = 'EPSG:6933'  # WGS 84 / NSIDC EASE-Grid 2.0 Global

print("\nClipping reservoirs to Africa (centroid-in-polygon)...")
res_proj = gdf_res.to_crs(EQUAL_AREA_CRS)
res_centroids = res_proj.copy()
res_centroids['geometry'] = res_proj.geometry.centroid
res_centroids = res_centroids.to_crs(gdf_africa.crs)

africa_res = gpd.sjoin(
    res_centroids,
    gdf_africa[['geometry']],
    how='inner',
    predicate='within'
)
africa_res_ids = set(africa_res['GDW_ID'])
gdf_res_africa = gdf_res[gdf_res['GDW_ID'].isin(africa_res_ids)].copy()
print(f"  {len(gdf_res_africa):,} reservoirs in Africa")

print("Clipping barriers to Africa (point-in-polygon)...")
africa_bar = gpd.sjoin(
    gdf_bar[['GDW_ID', 'geometry']],
    gdf_africa[['geometry']],
    how='inner',
    predicate='within'
)
africa_bar_ids = set(africa_bar['GDW_ID'])
print(f"  {len(africa_bar_ids):,} unique dam GDW_IDs in Africa")

# ---------------------------------------------------------------------------
# Find reservoirs with no matching barrier
# ---------------------------------------------------------------------------
res_without_dam_ids = africa_res_ids - africa_bar_ids
gdf_no_dam = gdf_res_africa[gdf_res_africa['GDW_ID'].isin(res_without_dam_ids)].copy()

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
n_total = len(gdf_res_africa)
n_no_dam = len(gdf_no_dam)
n_with_dam = n_total - n_no_dam

print("\n" + "=" * 60)
print("RESULTS: Africa GDW Reservoirs vs. Barriers")
print("=" * 60)
print(f"Total reservoirs in Africa       : {n_total:,}")
print(f"  With a GDW barrier (dam)       : {n_with_dam:,}  ({100*n_with_dam/n_total:.1f}%)")
print(f"  Without a GDW barrier (no dam) : {n_no_dam:,}  ({100*n_no_dam/n_total:.1f}%)")

if n_no_dam > 0:
    print("\nReservoirs without a dam (detail):")
    detail_cols = ['GDW_ID', 'RES_NAME', 'DAM_NAME', 'DAM_TYPE', 'LAKE_CTRL',
                   'COUNTRY', 'YEAR_DAM', 'AREA_SKM', 'MAIN_USE', 'COMMENTS']
    avail = [c for c in detail_cols if c in gdf_no_dam.columns]
    print(gdf_no_dam[avail].to_string(index=False))

print("\nReservoirs WITHOUT a dam, by country:")
country_counts = (
    gdf_no_dam.groupby('COUNTRY')
    .size()
    .rename('n_no_dam')
)
total_by_country = (
    gdf_res_africa.groupby('COUNTRY')
    .size()
    .rename('n_total')
)
summary = pd.concat([country_counts, total_by_country], axis=1).fillna(0).astype(int)
summary['pct_no_dam'] = (summary['n_no_dam'] / summary['n_total'] * 100).round(1)
summary = summary[summary['n_no_dam'] > 0].sort_values('n_no_dam', ascending=False)
if summary.empty:
    print("  None — all Africa reservoirs have a corresponding dam barrier.")
else:
    print(summary.to_string())
