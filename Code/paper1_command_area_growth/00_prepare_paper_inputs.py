"""Prepare or validate processed inputs required by the Paper 1 workflow.

This script covers the raw-to-processed dependencies needed before the canonical
inside/outside command-area analysis can run:

1. SSA arid country mask
   Raw/processed provenance: Code/0_process_data/2_Aridity_Refinement.ipynb
   Canonical output: config key SSA_All_by_Country_shp_path

2. GDW arid-SSA dams and GDW irrigation dams > 15 m
   Raw/processed provenance: Code/0_process_data/5_GDW_Dams_Processing.ipynb
   Canonical outputs: GDW_Arid_SSA_Final_shp_path and GDW_Arid_SSA_Final_Irr_shp_path

Command-area polygons and AEI rasters are consumed directly by the paper scripts,
so this script validates their presence but does not rewrite them.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import shapes
from rasterio.mask import mask
from shapely.geometry import shape
from shapely.ops import unary_union


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from paper1_common import (
    AEI_YEARS,
    WorkflowInputError,
    available_aei_years,
    config_path,
    ensure_paper_dirs,
    existing_aei_raster_path,
    find_column,
    find_vector_path,
    first_existing_vector,
)

from Code.utils.utility import ssa_iso


COMMAND_AREA_KEYS = (
    "No_Crop_Vectorized_Command_Area_shp_path",
    "No_Crop_Initial_CA_shp_path",
    "No_Crop_All_Height_Initial_CA_shp_path",
)


def _repair_geometry(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    out = gdf.copy()
    try:
        from shapely import make_valid

        out["geometry"] = out.geometry.apply(
            lambda geom: make_valid(geom) if geom is not None and not geom.is_valid else geom
        )
    except Exception:
        out["geometry"] = out.geometry.buffer(0)
    return out[out.geometry.notna() & ~out.geometry.is_empty].copy()


def _write_vector(gdf: gpd.GeoDataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(path)


def _load_africa_boundaries(target_crs: str | None = None) -> gpd.GeoDataFrame:
    source = find_vector_path("Africa_boundaries_shp_path", preferred_stems=("Africa_Countries",))
    africa = gpd.read_file(source.path)
    if africa.crs is None:
        raise WorkflowInputError(f"Africa boundaries have no CRS: {source.path}")
    if "ISO_3DIGIT" in africa.columns and "ISO" not in africa.columns:
        africa = africa.rename(columns={"ISO_3DIGIT": "ISO"})
    if target_crs is not None:
        africa = africa.to_crs(target_crs)
    return _repair_geometry(africa)


def _ensure_africa_all_arid(overwrite: bool = False) -> Path:
    """Ensure the broad arid-Africa vector exists, building it from the raw raster if needed."""

    out_path = config_path("Africa_All_shp_path")
    if out_path.exists() and not overwrite:
        return out_path

    raster_path = config_path("Global_Aridity_Raster_path")
    if not raster_path.exists():
        raise WorkflowInputError(f"Missing raw aridity raster: {raster_path}")

    print("Building Africa_All aridity layer from raw aridity raster. This can take a while.")
    with rasterio.open(raster_path) as src:
        raster_crs = src.crs
        africa = _load_africa_boundaries(target_crs=src.crs)
        africa_union = unary_union(africa.geometry)
        masked, transform = mask(src, [africa_union], crop=True, nodata=src.nodata)
        band = masked[0]

        if src.nodata is not None:
            valid = band != src.nodata
        else:
            valid = np.isfinite(band)

        # Global Aridity Index v3 is stored as aridity * 10000 in this workflow.
        arid = valid & (band < 5000)
        geometries = [
            shape(geom)
            for geom, value in shapes(arid.astype("uint8"), mask=arid, transform=transform)
            if value == 1
        ]

    if not geometries:
        raise WorkflowInputError("No arid-region pixels were found while building Africa_All layer.")

    arid_gdf = gpd.GeoDataFrame(geometry=geometries, crs=raster_crs)
    arid_gdf = _repair_geometry(arid_gdf)
    arid_gdf = gpd.GeoDataFrame(geometry=[unary_union(arid_gdf.geometry)], crs=arid_gdf.crs)
    arid_gdf["arid_mask"] = 1
    _write_vector(arid_gdf, out_path)
    print(f"Wrote Africa_All aridity layer: {out_path}")
    return out_path


def ensure_ssa_arid_country_mask(overwrite: bool = False) -> Path:
    """Ensure SSA_All_by_Country_shp_path exists."""

    out_path = config_path("SSA_All_by_Country_shp_path")
    if out_path.exists() and not overwrite:
        print(f"Study mask exists: {out_path}")
        return out_path

    africa_all_path = _ensure_africa_all_arid(overwrite=overwrite)
    arid_africa = gpd.read_file(africa_all_path)
    if arid_africa.crs is None:
        raise WorkflowInputError(f"Arid Africa layer has no CRS: {africa_all_path}")

    africa = _load_africa_boundaries(target_crs=arid_africa.crs)
    iso_col = find_column(africa.columns, ("ISO", "ISO_3DIGIT", "ADM0_A3", "GID_0"), "country ISO")
    if iso_col != "ISO":
        africa = africa.rename(columns={iso_col: "ISO"})

    print("Building SSA arid country mask by intersecting Africa_All with country boundaries.")
    clipped = gpd.overlay(arid_africa, africa, how="intersection", keep_geom_type=False)
    if "ISO" not in clipped.columns:
        raise WorkflowInputError("Country ISO column was lost during aridity/country overlay.")
    clipped = clipped[clipped["ISO"].isin(ssa_iso)].copy()
    clipped = _repair_geometry(clipped)

    if clipped.empty:
        raise WorkflowInputError("SSA arid country mask is empty after overlay/filtering.")

    _write_vector(clipped, out_path)
    print(f"Wrote SSA arid country mask: {out_path}")
    return out_path


def ensure_gdw_dam_outputs(overwrite: bool = False, min_height_m: float = 15.0) -> tuple[Path, Path]:
    """Ensure processed GDW arid-SSA dam outputs exist."""

    all_out = config_path("GDW_Arid_SSA_Final_shp_path")
    irr_out = config_path("GDW_Arid_SSA_Final_Irr_shp_path")
    if all_out.exists() and irr_out.exists() and not overwrite:
        print(f"GDW processed dam layers exist: {all_out} and {irr_out}")
        return all_out, irr_out

    raw_source = find_vector_path("GDW_barrier_shp_path")
    mask_path = ensure_ssa_arid_country_mask(overwrite=False)
    dams = gpd.read_file(raw_source.path)
    mask_gdf = gpd.read_file(mask_path)

    if dams.empty:
        raise WorkflowInputError(f"Raw GDW barriers are empty: {raw_source.path}")
    if mask_gdf.empty:
        raise WorkflowInputError(f"SSA arid mask is empty: {mask_path}")
    if dams.crs is None:
        raise WorkflowInputError(f"Raw GDW barriers have no CRS: {raw_source.path}")
    if mask_gdf.crs is None:
        raise WorkflowInputError(f"SSA arid mask has no CRS: {mask_path}")

    mask_gdf = mask_gdf.to_crs(dams.crs)
    mask_iso = find_column(mask_gdf.columns, ("ISO", "ISO_3DIGIT", "ADM0_A3", "GID_0"), "mask ISO")
    if mask_iso != "ISO":
        mask_gdf = mask_gdf.rename(columns={mask_iso: "ISO"})

    dam_id_col = find_column(dams.columns, ("GDW_ID", "GDWID", "dam_id", "DAM_ID"), "GDW dam id")
    year_col = find_column(dams.columns, ("YEAR_DAM", "YEAR", "Year", "yr", "commission_year"), "dam year")
    main_use_col = find_column(dams.columns, ("MAIN_USE", "main_use", "PURPOSE", "purpose"), "GDW main use")
    height_col = find_column(dams.columns, ("DAM_HGT_M", "HEIGHT", "DAM_HEIGHT", "height_m"), "GDW dam height")

    print("Spatially filtering raw GDW barriers to arid SSA.")
    joined = gpd.sjoin(
        dams,
        mask_gdf[["ISO", "geometry"]],
        how="inner",
        predicate="intersects",
    )
    if "ISO_right" in joined.columns:
        joined["ISO"] = joined["ISO_right"]
    elif "ISO" not in joined.columns and "ISO_left" in joined.columns:
        joined["ISO"] = joined["ISO_left"]
    joined = joined.drop(columns=[c for c in ("index_right",) if c in joined.columns])
    joined = joined.drop_duplicates(subset=[dam_id_col]).copy()
    joined[year_col] = pd.to_numeric(joined[year_col], errors="coerce")
    joined[height_col] = pd.to_numeric(joined[height_col], errors="coerce")
    joined = _repair_geometry(joined)

    if joined.empty:
        raise WorkflowInputError("No GDW barriers intersected the SSA arid country mask.")

    all_out.parent.mkdir(parents=True, exist_ok=True)
    joined.to_file(all_out)
    print(f"Wrote GDW arid-SSA dam layer: {all_out} ({len(joined):,} features)")

    irrigation = joined[
        joined[main_use_col].astype(str).str.contains("Irrigation", case=False, na=False)
        & (joined[height_col] > min_height_m)
    ].copy()
    if irrigation.empty:
        raise WorkflowInputError(
            f"GDW irrigation dam filter produced zero features. "
            f"Checked {main_use_col} contains Irrigation and {height_col} > {min_height_m}."
        )

    irrigation.to_file(irr_out)
    print(f"Wrote GDW arid-SSA irrigation dam layer: {irr_out} ({len(irrigation):,} features)")
    return all_out, irr_out


def validate_direct_inputs(years: list[int]) -> None:
    """Validate inputs consumed directly by Paper 1 scripts."""

    ca_source = first_existing_vector(COMMAND_AREA_KEYS)
    print(f"Command-area raw input found: {ca_source.path}")

    available = set(available_aei_years(AEI_YEARS))
    missing = [year for year in years if year not in available]
    if missing:
        missing_paths = ", ".join(str(config_path(f"Africa_AEI_{year}_asc_path")) for year in missing)
        raise WorkflowInputError(f"Missing AEI rasters for requested years {missing}: {missing_paths}")
    print(f"AEI raw rasters found for requested years: {', '.join(map(str, years))}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--years", nargs="+", default=None, help="Years expected by the paper run. Default: all AEI years.")
    parser.add_argument("--overwrite", action="store_true", help="Rebuild processed inputs even when outputs exist.")
    parser.add_argument("--min-dam-height-m", type=float, default=15.0, help="Minimum GDW dam height for irrigation layer.")
    args = parser.parse_args(argv)

    years = [int(y) for y in args.years] if args.years else list(AEI_YEARS)
    ensure_paper_dirs()
    ensure_ssa_arid_country_mask(overwrite=args.overwrite)
    ensure_gdw_dam_outputs(overwrite=args.overwrite, min_height_m=args.min_dam_height_m)
    validate_direct_inputs(years)
    print("Paper 1 inputs are ready.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except WorkflowInputError as exc:
        raise SystemExit(f"ERROR: {exc}") from None
