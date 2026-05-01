"""Extract gridded AEI inside/outside yearly command areas by country.

Primary output:
Data/Processed/Paper1_CommandAreaGrowth/final_tables/inside_outside_irrigation_by_country_year.csv

The script treats AEI raster cell values as hectares of area equipped for
irrigation, matching the legacy notebooks. Country masks come from the arid-SSA
country layer, so totals are for arid SSA portions of countries rather than whole
national territories.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.crs import CRS
from rasterio.features import geometry_mask


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from paper1_common import (
    COMMAND_AREA_LAYER,
    EXTRACTION_DIAGNOSTICS,
    YEARLY_COMMAND_AREA_INVENTORY,
    WorkflowInputError,
    config_path,
    ensure_paper_dirs,
    existing_aei_raster_path,
    extracted_irrigation_dir,
    final_tables_dir,
    find_column,
    parse_years,
    yearly_command_area_dir,
    yearly_command_area_path,
)


def _raster_crs(src) -> CRS:
    """Return raster CRS, correcting known missing/mislabelled AEI metadata."""

    if src.crs is None:
        return CRS.from_epsg(4326)
    bounds = src.bounds
    if src.crs.to_epsg() == 3857 and -180 <= bounds.left <= 180 and -90 <= bounds.bottom <= 90:
        return CRS.from_epsg(4326)
    return src.crs


def _read_raster_values(src) -> tuple[np.ndarray, np.ndarray]:
    arr = src.read(1, masked=True).astype("float64")
    data = arr.filled(np.nan)
    if src.nodata is not None:
        data[data == src.nodata] = np.nan
    valid = np.isfinite(data)
    data = np.where(valid, data, 0.0)
    return data, valid


def _mask_for_geometries(geometries, out_shape, transform, all_touched: bool) -> np.ndarray:
    geoms = [geom for geom in geometries if geom is not None and not geom.is_empty]
    if not geoms:
        return np.zeros(out_shape, dtype=bool)
    return geometry_mask(
        geoms,
        out_shape=out_shape,
        transform=transform,
        invert=True,
        all_touched=all_touched,
    )


def extract_year(
    year: int,
    raster_path: Path,
    command_area_path: Path,
    countries: gpd.GeoDataFrame,
    iso_col: str,
    country_col: str,
    all_touched: bool,
) -> tuple[list[dict], dict]:
    """Extract one year and return panel rows plus diagnostics."""

    if not command_area_path.exists():
        raise WorkflowInputError(f"Missing yearly command-area layer for {year}: {command_area_path}")

    command_area = gpd.read_file(command_area_path, layer=COMMAND_AREA_LAYER)
    with rasterio.open(raster_path) as src:
        raster_crs = _raster_crs(src)
        data, valid = _read_raster_values(src)
        countries_r = countries.to_crs(raster_crs)
        command_area_r = command_area.to_crs(raster_crs)

        ca_mask = _mask_for_geometries(command_area_r.geometry, data.shape, src.transform, all_touched)

        rows: list[dict] = []
        for _, country in countries_r.iterrows():
            country_mask = _mask_for_geometries([country.geometry], data.shape, src.transform, all_touched)
            mask_total = country_mask & valid
            if not mask_total.any():
                total = inside = outside = 0.0
                n_pixels = n_inside_pixels = 0
            else:
                mask_inside = mask_total & ca_mask
                total = float(data[mask_total].sum())
                inside = float(data[mask_inside].sum())
                outside = float(total - inside)
                n_pixels = int(mask_total.sum())
                n_inside_pixels = int(mask_inside.sum())

            inside_share = inside / total if total > 0 else np.nan
            rows.append(
                {
                    "year": year,
                    "ISO": country.get(iso_col),
                    "country_name": country.get(country_col),
                    "inside_AEI_ha": inside,
                    "outside_AEI_ha": outside,
                    "total_AEI_ha": total,
                    "inside_share": inside_share,
                    "outside_share": 1 - inside_share if total > 0 else np.nan,
                    "raster_path": str(raster_path),
                    "command_area_path": str(command_area_path),
                    "n_country_pixels": n_pixels,
                    "n_inside_pixels": n_inside_pixels,
                    "all_touched": all_touched,
                    "value_units_assumed": "ha",
                }
            )

        diagnostics = {
            "year": year,
            "raster_path": str(raster_path),
            "command_area_path": str(command_area_path),
            "raster_crs_used": str(raster_crs),
            "raster_width": src.width,
            "raster_height": src.height,
            "raw_valid_value_sum": float(data[valid].sum()),
            "panel_total_AEI_ha": float(sum(row["total_AEI_ha"] for row in rows)),
            "panel_inside_AEI_ha": float(sum(row["inside_AEI_ha"] for row in rows)),
            "panel_outside_AEI_ha": float(sum(row["outside_AEI_ha"] for row in rows)),
            "all_touched": all_touched,
        }

    return rows, diagnostics


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--years", nargs="+", default=None, help="Analysis years to extract. Default: 1980 1985 ... 2015.")
    parser.add_argument("--country-key", default="SSA_All_by_Country_shp_path", help="Config key for country/arid mask layer.")
    parser.add_argument("--iso-column", default=None, help="Country ISO column. Default: auto-detect ISO.")
    parser.add_argument("--country-column", default=None, help="Country name column. Default: auto-detect.")
    parser.add_argument("--all-touched", action="store_true", help="Use all raster cells touched by polygons.")
    args = parser.parse_args(argv)

    ensure_paper_dirs()
    years = parse_years(args.years)

    country_path = config_path(args.country_key)
    countries = gpd.read_file(country_path)
    if countries.empty:
        raise WorkflowInputError(f"Country layer is empty: {country_path}")
    if countries.crs is None:
        raise WorkflowInputError(f"Country layer has no CRS: {country_path}")

    iso_col = args.iso_column or find_column(countries.columns, ("ISO", "iso", "GID_0", "ADM0_A3"), "country ISO")
    country_col = args.country_column or find_column(
        countries.columns,
        ("NAME", "Country", "country", "ADM0_NAME", "NAME_LONG", "SOVEREIGNT", "admin"),
        "country name",
    )

    inventory_path = final_tables_dir() / YEARLY_COMMAND_AREA_INVENTORY
    command_inventory = pd.read_csv(inventory_path) if inventory_path.exists() else pd.DataFrame()

    panel_rows: list[dict] = []
    diagnostics_rows: list[dict] = []
    skipped: list[str] = []

    for year in years:
        raster_path = existing_aei_raster_path(year)
        if raster_path is None:
            skipped.append(f"{year}: missing raw AEI raster")
            continue
        ca_path = yearly_command_area_path(year, yearly_command_area_dir())
        if not ca_path.exists():
            skipped.append(f"{year}: missing yearly command-area layer")
            continue

        print(f"[{year}] Extracting AEI inside/outside command areas...", flush=True)
        rows, diagnostics = extract_year(
            year=year,
            raster_path=raster_path,
            command_area_path=ca_path,
            countries=countries,
            iso_col=iso_col,
            country_col=country_col,
            all_touched=args.all_touched,
        )
        panel_rows.extend(rows)
        diagnostics_rows.append(diagnostics)
        print(
            f"[{year}] Done. total={diagnostics['panel_total_AEI_ha']:.2f} ha, "
            f"inside={diagnostics['panel_inside_AEI_ha']:.2f} ha, "
            f"outside={diagnostics['panel_outside_AEI_ha']:.2f} ha",
            flush=True,
        )

    if not panel_rows:
        details = "\n- ".join(skipped) if skipped else "No requested years were processed."
        raise WorkflowInputError(f"No inside/outside AEI rows were produced.\n- {details}")

    panel = pd.DataFrame(panel_rows)
    if not command_inventory.empty:
        keep_cols = [c for c in ("year", "n_unique_dams", "command_area_ha", "status") if c in command_inventory.columns]
        panel = panel.merge(command_inventory[keep_cols], on="year", how="left")
        panel = panel.rename(columns={"n_unique_dams": "active_dam_count"})

    panel_path = config_path("Paper1_inside_outside_panel_csv_path")
    panel_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(panel_path, index=False)

    diagnostics = pd.DataFrame(diagnostics_rows)
    diag_path = extracted_irrigation_dir() / EXTRACTION_DIAGNOSTICS
    diagnostics.to_csv(diag_path, index=False)

    print(f"Wrote inside/outside panel: {panel_path}")
    print(f"Wrote extraction diagnostics: {diag_path}")
    if skipped:
        print("Skipped years:")
        for item in skipped:
            print(f"  - {item}")
    summary = panel.groupby("year")[["inside_AEI_ha", "outside_AEI_ha", "total_AEI_ha"]].sum().round(2)
    print(summary.to_string())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except WorkflowInputError as exc:
        raise SystemExit(f"ERROR: {exc}") from None
