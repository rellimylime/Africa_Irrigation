"""Build active, overlap-free command-area layers by analysis year.

Primary output:
Data/Processed/Paper1_CommandAreaGrowth/yearly_command_areas/command_areas_<year>.gpkg

The script maps command-area polygons to GDW dam commissioning years, keeps only
command areas attached to dams active by each analysis year, dissolves overlaps
with a unary union, and writes a compact inventory table for later joins.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.ops import unary_union


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from paper1_common import (
    AFRICA_EQUAL_AREA_CRS,
    COMMAND_AREA_LAYER,
    YEARLY_COMMAND_AREA_INVENTORY,
    WorkflowInputError,
    config_path,
    ensure_paper_dirs,
    final_tables_dir,
    find_column,
    find_vector_path,
    first_existing_vector,
    parse_years,
    yearly_command_area_dir,
    yearly_command_area_path,
)


DEFAULT_COMMAND_AREA_KEYS = (
    "No_Crop_Vectorized_Command_Area_shp_path",
    "No_Crop_Initial_CA_shp_path",
    "No_Crop_All_Height_Initial_CA_shp_path",
)


def _repair_geometry(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Repair invalid geometries with shapely.make_valid when available."""

    out = gdf.copy()
    try:
        from shapely import make_valid

        out["geometry"] = out.geometry.apply(
            lambda geom: make_valid(geom) if geom is not None and not geom.is_valid else geom
        )
    except Exception:
        out["geometry"] = out.geometry.buffer(0)
    out = out[out.geometry.notna() & ~out.geometry.is_empty].copy()
    return out


def _normalise_id(series: pd.Series) -> pd.Series:
    """Normalize dam ids across shapefile numeric/string driver quirks."""

    return (
        series.astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
    )


def _source_from_arg(path_or_key: str | None):
    if path_or_key is None:
        return first_existing_vector(DEFAULT_COMMAND_AREA_KEYS)

    if path_or_key in DEFAULT_COMMAND_AREA_KEYS:
        return find_vector_path(path_or_key)

    path = Path(path_or_key)
    if not path.is_absolute():
        candidate = config_path(path_or_key) if path_or_key.endswith("_path") else Path.cwd() / path
        path = candidate
    if not path.exists():
        raise WorkflowInputError(f"Command-area source does not exist: {path}")
    return type("VectorSourceLike", (), {"key": "custom", "path": path, "note": "custom path"})()


def build_yearly_command_areas(
    years: list[int],
    command_area_source,
    dam_source,
    output_dir: Path,
    target_crs: str,
    ca_id_column: str | None = None,
    dam_id_column: str | None = None,
    dam_year_column: str | None = None,
    overwrite: bool = False,
) -> pd.DataFrame:
    """Build one dissolved command-area layer per year and return inventory rows."""

    print(f"Loading command areas: {command_area_source.path}", flush=True)
    ca = gpd.read_file(command_area_source.path)
    print(f"Loading dams: {dam_source.path}", flush=True)
    dams = gpd.read_file(dam_source.path)

    if ca.empty:
        raise WorkflowInputError(f"Command-area source is empty: {command_area_source.path}")
    if dams.empty:
        raise WorkflowInputError(f"Dam source is empty: {dam_source.path}")

    ca_id = ca_id_column or find_column(ca.columns, ("GDW_ID", "GDWID", "dam_id", "DAM_ID"), "command-area dam id")
    dam_id = dam_id_column or find_column(dams.columns, ("GDW_ID", "GDWID", "dam_id", "DAM_ID"), "dam id")
    dam_year = dam_year_column or find_column(
        dams.columns,
        ("YEAR_DAM", "YEAR", "Year", "yr", "commission", "commission_year"),
        "dam commissioning year",
    )

    ca = ca[[ca_id, "geometry"]].copy()
    dams = dams[[dam_id, dam_year, "geometry"]].copy()
    dams[dam_year] = pd.to_numeric(dams[dam_year], errors="coerce")
    dams["_dam_id_norm"] = _normalise_id(dams[dam_id])
    dams = dams.dropna(subset=[dam_year])

    dam_years = dams.drop_duplicates(subset=["_dam_id_norm"]).set_index("_dam_id_norm")[dam_year].to_dict()
    ca["source_dam_id"] = _normalise_id(ca[ca_id])
    ca["dam_year"] = pd.to_numeric(ca["source_dam_id"].map(dam_years), errors="coerce")
    ca = ca.dropna(subset=["dam_year"]).copy()

    if ca.empty:
        raise WorkflowInputError(
            "No command-area polygons could be matched to dam commissioning years. "
            f"Check {ca_id} in command areas and {dam_id}/{dam_year} in dams."
        )

    if ca.crs is None:
        raise WorkflowInputError(f"Command-area source has no CRS: {command_area_source.path}")
    print(f"Matched command areas to dam years: {len(ca):,} polygons", flush=True)
    print(f"Repairing/reprojecting command-area geometries to {target_crs}", flush=True)
    ca = _repair_geometry(ca.to_crs(target_crs))

    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []

    for year in years:
        out_path = yearly_command_area_path(year, output_dir)
        print(f"[{year}] Selecting active command areas...", flush=True)
        active = ca[ca["dam_year"] <= year].copy()
        active = active[active.geometry.notna() & ~active.geometry.is_empty].copy()

        row = {
            "year": year,
            "source_key": command_area_source.key,
            "source_path": str(command_area_source.path),
            "dam_source_path": str(dam_source.path),
            "target_crs": target_crs,
            "output_path": str(out_path),
            "n_source_polygons": int(len(active)),
            "n_unique_dams": int(active["source_dam_id"].nunique()) if not active.empty else 0,
            "dam_year_min": float(active["dam_year"].min()) if not active.empty else pd.NA,
            "dam_year_max": float(active["dam_year"].max()) if not active.empty else pd.NA,
            "command_area_ha": 0.0,
            "status": "empty",
        }

        if active.empty:
            print(f"[{year}] No active command areas; skipping layer write.", flush=True)
            rows.append(row)
            continue

        if out_path.exists() and not overwrite:
            print(f"[{year}] Output exists and --overwrite was not set: {out_path}", flush=True)
            row["status"] = "exists_not_overwritten"
            try:
                existing = gpd.read_file(out_path, layer=COMMAND_AREA_LAYER)
                row["command_area_ha"] = float(existing.to_crs(target_crs).geometry.area.sum() / 10_000)
            except Exception:
                pass
            rows.append(row)
            continue

        print(f"[{year}] Dissolving {len(active):,} polygons from {active['source_dam_id'].nunique():,} dams...", flush=True)
        merged = unary_union(active.geometry)
        out = gpd.GeoDataFrame(
            {
                "year": [year],
                "n_src_poly": [int(len(active))],
                "n_dams": [int(active["source_dam_id"].nunique())],
                "dam_year_min": [float(active["dam_year"].min())],
                "dam_year_max": [float(active["dam_year"].max())],
                "source_key": [command_area_source.key],
            },
            geometry=[merged],
            crs=target_crs,
        )
        out["command_area_ha"] = out.geometry.area / 10_000
        print(f"[{year}] Writing {out_path}", flush=True)
        out.to_file(out_path, layer=COMMAND_AREA_LAYER, driver="GPKG")

        row["command_area_ha"] = float(out["command_area_ha"].iloc[0])
        row["status"] = "written"
        print(f"[{year}] Done. command_area_ha={row['command_area_ha']:.2f}", flush=True)
        rows.append(row)

    return pd.DataFrame(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--years", nargs="+", default=None, help="Analysis years to build. Default: 1980 1985 ... 2015.")
    parser.add_argument(
        "--command-area",
        default=None,
        help="Optional command-area config key or file path. Default: first available command-area source.",
    )
    parser.add_argument(
        "--dam-key",
        default="GDW_Arid_SSA_Final_Irr_shp_path",
        help="Config key for the dam layer used to assign commissioning years.",
    )
    parser.add_argument("--ca-id-column", default=None, help="Command-area dam id column. Default: auto-detect GDW_ID.")
    parser.add_argument("--dam-id-column", default=None, help="Dam id column. Default: auto-detect GDW_ID.")
    parser.add_argument("--dam-year-column", default=None, help="Dam commissioning year column. Default: auto-detect YEAR_DAM.")
    parser.add_argument("--target-crs", default=AFRICA_EQUAL_AREA_CRS, help="Output vector CRS.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing yearly GeoPackages.")
    args = parser.parse_args(argv)

    ensure_paper_dirs()
    years = parse_years(args.years)
    ca_source = _source_from_arg(args.command_area)
    dam_source = find_vector_path(args.dam_key)
    output_dir = yearly_command_area_dir()

    inventory = build_yearly_command_areas(
        years=years,
        command_area_source=ca_source,
        dam_source=dam_source,
        output_dir=output_dir,
        target_crs=args.target_crs,
        ca_id_column=args.ca_id_column,
        dam_id_column=args.dam_id_column,
        dam_year_column=args.dam_year_column,
        overwrite=args.overwrite,
    )

    inventory_path = final_tables_dir() / YEARLY_COMMAND_AREA_INVENTORY
    inventory.to_csv(inventory_path, index=False)
    print(f"Wrote yearly command-area inventory: {inventory_path}")
    print(inventory[["year", "status", "n_source_polygons", "n_unique_dams", "command_area_ha"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except WorkflowInputError as exc:
        raise SystemExit(f"ERROR: {exc}") from None
