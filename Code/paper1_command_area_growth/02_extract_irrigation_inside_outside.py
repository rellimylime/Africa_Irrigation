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
import math
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.crs import CRS
from rasterio.features import geometry_mask
from rasterio.windows import from_bounds
from shapely.geometry import box
from shapely.ops import unary_union


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from paper1_common import (
    AFRICA_EQUAL_AREA_CRS,
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


EXTRACTION_METHOD_MASK = "raster_mask"
EXTRACTION_METHOD_AREA_WEIGHTED = "area_weighted"


def _tagged_csv_path(path: Path, output_tag: str | None) -> Path:
    """Return a variant-specific CSV path without changing canonical defaults."""

    if output_tag is None:
        return path
    tag = output_tag.strip().replace("-", "_")
    if not tag or not tag.replace("_", "").isalnum():
        raise WorkflowInputError(
            f"Output tag must use only letters, numbers, underscores, or hyphens: {output_tag!r}"
        )
    return path.with_name(f"{path.stem}_{tag}{path.suffix}")


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


def _clipped_window(bounds, transform, width: int, height: int):
    """Return an integer raster window covering bounds, clipped to raster extent."""

    raw = from_bounds(*bounds, transform=transform)
    row_start = max(0, math.floor(raw.row_off))
    row_stop = min(height, math.ceil(raw.row_off + raw.height))
    col_start = max(0, math.floor(raw.col_off))
    col_stop = min(width, math.ceil(raw.col_off + raw.width))
    if row_start >= row_stop or col_start >= col_stop:
        return None
    return row_start, row_stop, col_start, col_stop


def _cell_polygons(transform, rows: np.ndarray, cols: np.ndarray) -> list:
    """Build raster-cell polygons in the raster CRS for absolute row/col indices."""

    geoms = []
    for row, col in zip(rows, cols):
        x0, y0 = transform * (int(col), int(row))
        x1, y1 = transform * (int(col) + 1, int(row) + 1)
        geoms.append(box(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)))
    return geoms


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


def _prepare_country_masks(countries: gpd.GeoDataFrame, iso_col: str, country_col: str) -> gpd.GeoDataFrame:
    """Dissolve arid-country fragments to one non-overlapping mask per ISO."""

    keep = countries[[iso_col, country_col, "geometry"]].copy()
    keep = keep.rename(columns={iso_col: "ISO", country_col: "country_name"})
    keep["ISO"] = keep["ISO"].astype(str).str.strip().replace({"nan": "", "None": ""})
    keep = keep[keep["ISO"].notna() & keep["ISO"].ne("") & keep.geometry.notna()].copy()
    keep = _repair_geometry(keep)
    if keep.empty:
        raise WorkflowInputError("Country mask has no usable country geometries after geometry repair.")

    names = keep.groupby("ISO", dropna=False)["country_name"].agg(
        lambda values: next(
            (
                str(value)
                for value in values
                if pd.notna(value) and str(value).strip() and str(value).strip().lower() not in {"nan", "none"}
            ),
            "",
        )
    ).reset_index()
    dissolved = keep[["ISO", "geometry"]].dissolve(by="ISO", as_index=False)
    dissolved = dissolved.merge(names, on="ISO", how="left")
    dissolved = _repair_geometry(dissolved)
    return dissolved[["ISO", "country_name", "geometry"]]


def _extract_area_weighted_country(
    country_r,
    country_eq_geometry,
    command_area_eq_geometry,
    data: np.ndarray,
    valid: np.ndarray,
    transform,
    raster_crs: CRS,
) -> dict:
    """Extract AEI using exact fractional overlap of raster cells with vector masks."""

    window = _clipped_window(country_r.geometry.bounds, transform, data.shape[1], data.shape[0])
    if window is None:
        return {
            "total": 0.0,
            "inside": 0.0,
            "outside": 0.0,
            "n_pixels": 0,
            "n_inside_pixels": 0,
            "country_cell_fraction_sum": 0.0,
            "inside_cell_fraction_sum": 0.0,
        }

    row_start, row_stop, col_start, col_stop = window
    data_window = data[row_start:row_stop, col_start:col_stop]
    valid_window = valid[row_start:row_stop, col_start:col_stop]
    candidate = valid_window & (data_window != 0)
    if not candidate.any():
        return {
            "total": 0.0,
            "inside": 0.0,
            "outside": 0.0,
            "n_pixels": 0,
            "n_inside_pixels": 0,
            "country_cell_fraction_sum": 0.0,
            "inside_cell_fraction_sum": 0.0,
        }

    local_rows, local_cols = np.where(candidate)
    abs_rows = local_rows + row_start
    abs_cols = local_cols + col_start
    values = data_window[local_rows, local_cols].astype("float64")
    cells = gpd.GeoDataFrame(
        {"value": values},
        geometry=_cell_polygons(transform, abs_rows, abs_cols),
        crs=raster_crs,
    ).to_crs(AFRICA_EQUAL_AREA_CRS)

    cell_area = cells.geometry.area.to_numpy()
    country_area = cells.geometry.intersection(country_eq_geometry).area.to_numpy()
    country_fraction = np.divide(country_area, cell_area, out=np.zeros_like(country_area), where=cell_area > 0)
    country_fraction = np.clip(country_fraction, 0.0, 1.0)
    keep = country_fraction > 0
    if not keep.any():
        return {
            "total": 0.0,
            "inside": 0.0,
            "outside": 0.0,
            "n_pixels": 0,
            "n_inside_pixels": 0,
            "country_cell_fraction_sum": 0.0,
            "inside_cell_fraction_sum": 0.0,
        }

    values_keep = values[keep]
    cell_area_keep = cell_area[keep]
    country_fraction_keep = country_fraction[keep]
    total = float(np.dot(values_keep, country_fraction_keep))
    inside = 0.0
    inside_fraction = np.zeros_like(country_fraction_keep)

    if command_area_eq_geometry is not None and not command_area_eq_geometry.is_empty:
        inside_geometry = country_eq_geometry.intersection(command_area_eq_geometry)
        if not inside_geometry.is_empty:
            cells_keep = cells.loc[keep]
            inside_area = cells_keep.geometry.intersection(inside_geometry).area.to_numpy()
            inside_fraction = np.divide(
                inside_area,
                cell_area_keep,
                out=np.zeros_like(inside_area),
                where=cell_area_keep > 0,
            )
            inside_fraction = np.minimum(np.clip(inside_fraction, 0.0, 1.0), country_fraction_keep)
            inside = float(np.dot(values_keep, inside_fraction))

    outside = total - inside
    if abs(outside) < 1e-9:
        outside = 0.0
    return {
        "total": total,
        "inside": inside,
        "outside": outside,
        "n_pixels": int(keep.sum()),
        "n_inside_pixels": int((inside_fraction > 0).sum()),
        "country_cell_fraction_sum": float(country_fraction_keep.sum()),
        "inside_cell_fraction_sum": float(inside_fraction.sum()),
    }


def extract_year(
    year: int,
    raster_path: Path,
    command_area_path: Path,
    countries: gpd.GeoDataFrame,
    all_touched: bool,
    area_weighted: bool,
) -> tuple[list[dict], dict]:
    """Extract one year and return panel rows plus diagnostics."""

    if not command_area_path.exists():
        raise WorkflowInputError(f"Missing yearly command-area layer for {year}: {command_area_path}")

    command_area = gpd.read_file(command_area_path, layer=COMMAND_AREA_LAYER)
    with rasterio.open(raster_path) as src:
        raster_crs = _raster_crs(src)
        data, valid = _read_raster_values(src)
        countries_r = countries.to_crs(raster_crs)
        extraction_method = EXTRACTION_METHOD_AREA_WEIGHTED if area_weighted else EXTRACTION_METHOD_MASK
        if area_weighted:
            countries_eq = countries.to_crs(AFRICA_EQUAL_AREA_CRS)
            command_area_eq = _repair_geometry(command_area.to_crs(AFRICA_EQUAL_AREA_CRS))
            command_area_eq_geometry = unary_union(command_area_eq.geometry) if not command_area_eq.empty else None
            ca_mask = None
        else:
            countries_eq = None
            command_area_eq_geometry = None
            command_area_r = command_area.to_crs(raster_crs)
            ca_mask = _mask_for_geometries(command_area_r.geometry, data.shape, src.transform, all_touched)

        rows: list[dict] = []
        for idx, country in countries_r.iterrows():
            if area_weighted:
                result = _extract_area_weighted_country(
                    country_r=country,
                    country_eq_geometry=countries_eq.loc[idx].geometry,
                    command_area_eq_geometry=command_area_eq_geometry,
                    data=data,
                    valid=valid,
                    transform=src.transform,
                    raster_crs=raster_crs,
                )
                total = result["total"]
                inside = result["inside"]
                outside = result["outside"]
                n_pixels = result["n_pixels"]
                n_inside_pixels = result["n_inside_pixels"]
                country_cell_fraction_sum = result["country_cell_fraction_sum"]
                inside_cell_fraction_sum = result["inside_cell_fraction_sum"]
            else:
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
                country_cell_fraction_sum = np.nan
                inside_cell_fraction_sum = np.nan

            inside_share = inside / total if total > 0 else np.nan
            rows.append(
                {
                    "year": year,
                    "ISO": country.get("ISO"),
                    "country_name": country.get("country_name"),
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
                    "extraction_method": extraction_method,
                    "weighted_country_cell_fraction_sum": country_cell_fraction_sum,
                    "weighted_inside_cell_fraction_sum": inside_cell_fraction_sum,
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
            "n_country_masks": int(len(countries_r)),
            "all_touched": all_touched,
            "extraction_method": extraction_method,
        }

    return rows, diagnostics


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--years", nargs="+", default=None, help="Analysis years to extract. Default: 1980 1985 ... 2015.")
    parser.add_argument("--country-key", default="SSA_All_by_Country_shp_path", help="Config key for country/arid mask layer.")
    parser.add_argument("--iso-column", default=None, help="Country ISO column. Default: auto-detect ISO.")
    parser.add_argument("--country-column", default=None, help="Country name column. Default: auto-detect.")
    parser.add_argument("--all-touched", action="store_true", help="Use all raster cells touched by polygons.")
    parser.add_argument(
        "--area-weighted",
        action="store_true",
        help="Use fractional cell overlap with country and command-area polygons instead of a binary raster mask.",
    )
    parser.add_argument(
        "--output-tag",
        default=None,
        help="Write variant outputs with this tag instead of overwriting the canonical panel/diagnostics CSVs.",
    )
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
    input_country_features = len(countries)
    countries = _prepare_country_masks(countries, iso_col, country_col)
    print(
        f"Prepared country masks: dissolved {input_country_features:,} features "
        f"to {len(countries):,} ISO masks.",
        flush=True,
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

        method = EXTRACTION_METHOD_AREA_WEIGHTED if args.area_weighted else EXTRACTION_METHOD_MASK
        print(f"[{year}] Extracting AEI inside/outside command areas ({method})...", flush=True)
        rows, diagnostics = extract_year(
            year=year,
            raster_path=raster_path,
            command_area_path=ca_path,
            countries=countries,
            all_touched=args.all_touched,
            area_weighted=args.area_weighted,
        )
        panel_rows.extend(rows)
        diagnostics["n_country_features_input"] = input_country_features
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

    panel_path = _tagged_csv_path(config_path("Paper1_inside_outside_panel_csv_path"), args.output_tag)
    panel_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(panel_path, index=False)

    diagnostics = pd.DataFrame(diagnostics_rows)
    diag_path = _tagged_csv_path(extracted_irrigation_dir() / EXTRACTION_DIAGNOSTICS, args.output_tag)
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
