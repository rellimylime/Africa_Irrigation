"""Validate physical plausibility of modeled command areas with a local DEM.

The command-area export already uses elevation constraints in Earth Engine, so
this is not independent ground-truth validation. It is a reproducible QA layer:
using the local HDMA-derived DEM, it asks whether each modeled envelope is mostly
below the exported reservoir elevation threshold and whether reservoir elevation
metadata are broadly consistent with DEM elevations near the dam point.
"""

from __future__ import annotations

import argparse
import math
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", str(Path(os.environ.get("TMP", "C:/tmp")) / "paper1_matplotlib"))

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from affine import Affine
from rasterio.enums import Resampling
from rasterio.features import geometry_mask
from rasterio.windows import Window, from_bounds, transform as window_transform
from shapely.geometry.base import BaseGeometry


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from paper1_common import (  # noqa: E402
    AFRICA_EQUAL_AREA_CRS,
    WorkflowInputError,
    config_path,
    ensure_paper_dirs,
    final_tables_dir,
    find_column,
    find_vector_path,
    paper_dir,
)


END_YEAR = 2015
DEFAULT_TARGET_RESOLUTION_M = 250.0
ALLOWED_HEAD_TOLERANCE_M = 10.0

DETAIL_TABLE = "paper1_command_area_dem_plausibility_by_dam.csv"
SUMMARY_TABLE = "paper1_command_area_dem_plausibility_summary.csv"
FLAGGED_TABLE = "paper1_command_area_dem_plausibility_flagged.csv"


def _as_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _clean_id(value) -> str:
    if pd.isna(value):
        return ""
    try:
        numeric = float(value)
        if numeric.is_integer():
            return str(int(numeric))
    except (TypeError, ValueError):
        pass
    return str(value).strip()


def _safe_pct(mask: np.ndarray) -> float:
    if mask.size == 0:
        return np.nan
    return float(np.mean(mask) * 100)


def _percentile(values: np.ndarray, q: float) -> float:
    if values.size == 0:
        return np.nan
    return float(np.nanpercentile(values, q))


def _intersect_window(window: Window, width: int, height: int) -> Window | None:
    col0 = max(0, int(math.floor(window.col_off)))
    row0 = max(0, int(math.floor(window.row_off)))
    col1 = min(width, int(math.ceil(window.col_off + window.width)))
    row1 = min(height, int(math.ceil(window.row_off + window.height)))
    if col1 <= col0 or row1 <= row0:
        return None
    return Window(col0, row0, col1 - col0, row1 - row0)


def _read_dem_values_for_geometry(
    src: rasterio.io.DatasetReader,
    geom: BaseGeometry,
    target_resolution_m: float,
) -> tuple[np.ndarray, Affine]:
    """Return DEM values inside a geometry and the decimated output transform."""

    raw_window = from_bounds(*geom.bounds, transform=src.transform)
    window = _intersect_window(raw_window, src.width, src.height)
    if window is None:
        return np.array([], dtype=float), src.transform

    native_res = max(abs(src.transform.a), abs(src.transform.e))
    factor = max(1, int(math.ceil(target_resolution_m / native_res)))
    out_height = max(1, int(math.ceil(window.height / factor)))
    out_width = max(1, int(math.ceil(window.width / factor)))

    data = src.read(
        1,
        window=window,
        out_shape=(out_height, out_width),
        masked=True,
        resampling=Resampling.average,
    )
    base_transform = window_transform(window, src.transform)
    out_transform = base_transform * Affine.scale(window.width / out_width, window.height / out_height)

    inside = geometry_mask(
        [geom],
        out_shape=(out_height, out_width),
        transform=out_transform,
        invert=True,
        all_touched=True,
    )
    arr = np.asarray(data, dtype=float)
    mask = np.ma.getmaskarray(data)
    valid = inside & ~mask & np.isfinite(arr) & (arr > -500)
    return arr[valid], out_transform


def _dem_point_summary(
    src: rasterio.io.DatasetReader,
    point_geom: BaseGeometry | None,
    radius_pixels: int = 1,
) -> float:
    if point_geom is None or point_geom.is_empty:
        return np.nan
    try:
        row, col = src.index(point_geom.x, point_geom.y)
    except Exception:
        return np.nan
    row0 = max(0, row - radius_pixels)
    row1 = min(src.height, row + radius_pixels + 1)
    col0 = max(0, col - radius_pixels)
    col1 = min(src.width, col + radius_pixels + 1)
    if row1 <= row0 or col1 <= col0:
        return np.nan
    data = src.read(1, window=Window(col0, row0, col1 - col0, row1 - row0), masked=True)
    arr = np.asarray(data, dtype=float)
    valid = ~np.ma.getmaskarray(data) & np.isfinite(arr) & (arr > -500)
    if not np.any(valid):
        return np.nan
    return float(np.nanmedian(arr[valid]))


def _distance_metrics(
    transform: Affine,
    shape: tuple[int, int],
    valid_mask: np.ndarray,
    dam_geom: BaseGeometry | None,
    head_values_grid: np.ndarray,
) -> dict[str, float]:
    if dam_geom is None or dam_geom.is_empty or not np.any(valid_mask):
        return {
            "distance_median_m": np.nan,
            "distance_p95_m": np.nan,
            "distance_max_m": np.nan,
            "far_low_head_pct": np.nan,
        }

    rows, cols = np.indices(shape)
    xs = transform.c + transform.a * (cols + 0.5) + transform.b * (rows + 0.5)
    ys = transform.f + transform.d * (cols + 0.5) + transform.e * (rows + 0.5)
    dist = np.hypot(xs - dam_geom.x, ys - dam_geom.y)
    dist_valid = dist[valid_mask]
    head_valid = head_values_grid[valid_mask]
    far_low = (dist_valid > 25_000) & (head_valid < 0)
    return {
        "distance_median_m": _percentile(dist_valid, 50),
        "distance_p95_m": _percentile(dist_valid, 95),
        "distance_max_m": float(np.nanmax(dist_valid)) if dist_valid.size else np.nan,
        "far_low_head_pct": _safe_pct(far_low),
    }


def _sample_geometry_full(
    src: rasterio.io.DatasetReader,
    geom: BaseGeometry,
    res_elev_m: float,
    dam_geom: BaseGeometry | None,
    target_resolution_m: float,
) -> dict[str, float]:
    raw_window = from_bounds(*geom.bounds, transform=src.transform)
    window = _intersect_window(raw_window, src.width, src.height)
    if window is None:
        return {"dem_sample_cells": 0}

    native_res = max(abs(src.transform.a), abs(src.transform.e))
    factor = max(1, int(math.ceil(target_resolution_m / native_res)))
    out_height = max(1, int(math.ceil(window.height / factor)))
    out_width = max(1, int(math.ceil(window.width / factor)))

    data = src.read(
        1,
        window=window,
        out_shape=(out_height, out_width),
        masked=True,
        resampling=Resampling.average,
    )
    out_transform = window_transform(window, src.transform) * Affine.scale(window.width / out_width, window.height / out_height)
    inside = geometry_mask(
        [geom],
        out_shape=(out_height, out_width),
        transform=out_transform,
        invert=True,
        all_touched=True,
    )
    arr = np.asarray(data, dtype=float)
    valid_mask = inside & ~np.ma.getmaskarray(data) & np.isfinite(arr) & (arr > -500)
    elev = arr[valid_mask]
    if elev.size == 0 or not np.isfinite(res_elev_m):
        return {"dem_sample_cells": int(elev.size)}

    head = res_elev_m - elev
    head_grid = np.full(arr.shape, np.nan, dtype=float)
    head_grid[valid_mask] = arr[valid_mask]
    head_grid = res_elev_m - head_grid
    dist = _distance_metrics(out_transform, arr.shape, valid_mask, dam_geom, head_grid)

    metrics = {
        "dem_sample_cells": int(elev.size),
        "dem_target_resolution_m": float(target_resolution_m),
        "dem_elev_min_m": float(np.nanmin(elev)),
        "dem_elev_p05_m": _percentile(elev, 5),
        "dem_elev_p10_m": _percentile(elev, 10),
        "dem_elev_median_m": _percentile(elev, 50),
        "dem_elev_p90_m": _percentile(elev, 90),
        "dem_elev_p95_m": _percentile(elev, 95),
        "dem_elev_max_m": float(np.nanmax(elev)),
        "head_min_m": float(np.nanmin(head)),
        "head_p05_m": _percentile(head, 5),
        "head_p10_m": _percentile(head, 10),
        "head_median_m": _percentile(head, 50),
        "head_p90_m": _percentile(head, 90),
        "head_p95_m": _percentile(head, 95),
        "head_max_m": float(np.nanmax(head)),
        "pct_below_reservoir": _safe_pct(elev <= res_elev_m),
        "pct_below_reservoir_plus5m": _safe_pct(elev <= res_elev_m + 5),
        "pct_below_reservoir_plus10m": _safe_pct(elev <= res_elev_m + ALLOWED_HEAD_TOLERANCE_M),
        "pct_above_reservoir_plus10m": _safe_pct(elev > res_elev_m + ALLOWED_HEAD_TOLERANCE_M),
        "pct_positive_head": _safe_pct(head >= 0),
        "pct_head_ge_5m": _safe_pct(head >= 5),
    }
    metrics.update(dist)
    return metrics


def _load_command_areas() -> tuple[gpd.GeoDataFrame, Path]:
    source = find_vector_path("No_Crop_Vectorized_Command_Area_shp_path")
    ca = gpd.read_file(source.path)
    if ca.empty:
        raise WorkflowInputError(f"Command-area source is empty: {source.path}")
    if ca.crs is None:
        ca = ca.set_crs("EPSG:4326")
    return ca, source.path


def _load_dam_records(dem_crs) -> dict[str, dict]:
    dams = gpd.read_file(config_path("GDW_Arid_SSA_Final_Irr_shp_path"))
    if dams.empty:
        return {}
    if dams.crs is None:
        dams = dams.set_crs("EPSG:4326")
    dams = dams.to_crs(dem_crs)
    dam_id_col = find_column(dams.columns, ("GDW_ID", "GDWID", "dam_id", "DAM_ID"), "dam id")
    year_col = next((col for col in ("YEAR_DAM", "DAM_YEAR", "Year_Dam", "YEAR") if col in dams.columns), None)
    fallback_year_col = next((col for col in ("PRE_YEAR", "ALT_YEAR", "YEAR_TXT") if col in dams.columns), None)
    rem_col = next((col for col in ("REM_YEAR", "DAM_REM_YR", "REM_YR") if col in dams.columns), None)

    records: dict[str, dict] = {}
    for _, row in dams.iterrows():
        gdw_id = _clean_id(row[dam_id_col])
        year_value = pd.to_numeric(pd.Series([row[year_col]]), errors="coerce").iloc[0] if year_col else np.nan
        if not _is_valid_year(year_value) and fallback_year_col:
            year_value = pd.to_numeric(pd.Series([row[fallback_year_col]]), errors="coerce").iloc[0]
        records[gdw_id] = {
            "geometry": row.geometry,
            "year": year_value,
            "year_source": fallback_year_col if fallback_year_col and not _is_valid_year(pd.to_numeric(pd.Series([row[year_col]]), errors="coerce").iloc[0] if year_col else np.nan) and _is_valid_year(year_value) else year_col,
            "rem_year": pd.to_numeric(pd.Series([row[rem_col]]), errors="coerce").iloc[0] if rem_col else np.nan,
        }
    return records


def _active_by_year(ca: pd.DataFrame, year_col: str | None, rem_col: str | None, year: int) -> pd.Series:
    if year_col is None:
        return pd.Series(True, index=ca.index)
    built = _as_numeric(ca[year_col])
    built_valid = built.notna() & ~built.isin([-99, -999, -9999, 0])
    active = built_valid & built.le(year)
    if rem_col is not None:
        rem = _as_numeric(ca[rem_col])
        removed = rem.notna() & ~rem.isin([-99, -999, -9999, 0]) & rem.le(year)
        active = active & ~removed
    return active


def _is_valid_year(value) -> bool:
    return pd.notna(value) and float(value) not in {-99, -999, -9999, 0}


def _active_from_years(built_year, rem_year, analysis_year: int) -> bool | None:
    if not _is_valid_year(built_year):
        return None
    active = float(built_year) <= analysis_year
    if _is_valid_year(rem_year) and float(rem_year) <= analysis_year:
        active = False
    return bool(active)


def _validate(target_resolution_m: float, year: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ca, ca_path = _load_command_areas()
    res_col = find_column(ca.columns, ("ResElev", "RES_ELEV", "ELEV_MASL", "elev_masl"), "reservoir elevation")
    id_col = find_column(ca.columns, ("GDW_ID", "GDWID", "dam_id", "DAM_ID"), "command-area dam id")
    year_col = next((col for col in ("YEAR_DAM", "DAM_YEAR", "Year_Dam", "YEAR") if col in ca.columns), None)
    rem_col = next((col for col in ("REM_YEAR", "DAM_REM_YR", "REM_YR") if col in ca.columns), None)
    area_col = next((col for col in ("area", "AREA", "area_ha") if col in ca.columns), None)

    dem_path = config_path("Africa_Elevation_Reprojected_tif_path")
    if not dem_path.exists():
        raise WorkflowInputError(f"Missing local DEM: {dem_path}")

    with rasterio.open(dem_path) as src:
        if src.crs is None:
            raise WorkflowInputError(f"DEM has no CRS: {dem_path}")
        ca_dem = ca.to_crs(src.crs)
        dam_records = _load_dam_records(src.crs)

        rows: list[dict] = []
        fallback_active = _active_by_year(ca, year_col, rem_col, year)
        for idx, row in ca_dem.iterrows():
            gdw_id = _clean_id(ca.loc[idx, id_col])
            res_elev_m = pd.to_numeric(pd.Series([ca.loc[idx, res_col]]), errors="coerce").iloc[0]
            dam_record = dam_records.get(gdw_id, {})
            dam_geom = dam_record.get("geometry")
            active_from_dam = _active_from_years(dam_record.get("year", np.nan), dam_record.get("rem_year", np.nan), year)
            if active_from_dam is None:
                active_value = bool(fallback_active.loc[idx])
                active_source = "command_area_export_year"
            else:
                active_value = active_from_dam
                active_source = "processed_gdw_dam_year"
            metrics = _sample_geometry_full(
                src=src,
                geom=row.geometry,
                res_elev_m=float(res_elev_m) if pd.notna(res_elev_m) else np.nan,
                dam_geom=dam_geom,
                target_resolution_m=target_resolution_m,
            )
            dam_dem_m = _dem_point_summary(src, dam_geom)
            res_minus_dam_dem_m = (
                float(res_elev_m) - dam_dem_m if pd.notna(res_elev_m) and pd.notna(dam_dem_m) else np.nan
            )
            source_area_ha = np.nan
            if area_col is not None:
                raw_area = pd.to_numeric(pd.Series([ca.loc[idx, area_col]]), errors="coerce").iloc[0]
                if pd.notna(raw_area):
                    source_area_ha = float(raw_area) / 10_000 if raw_area > 10_000 else float(raw_area)

            rows.append(
                {
                    "GDW_ID": gdw_id,
                    "active_by_year": active_value,
                    "analysis_year": year,
                    "active_year_source": active_source,
                    "dam_year_used": dam_record.get("year", np.nan),
                    "dam_year_field_used": dam_record.get("year_source", ""),
                    "dam_rem_year_used": dam_record.get("rem_year", np.nan),
                    "source_area_ha": source_area_ha,
                    "res_elev_m": float(res_elev_m) if pd.notna(res_elev_m) else np.nan,
                    "dam_dem_median_3x3_m": dam_dem_m,
                    "res_minus_dam_dem_m": res_minus_dam_dem_m,
                    "source_command_area_path": str(ca_path),
                    "dem_path": str(dem_path),
                    **metrics,
                }
            )

    detail = pd.DataFrame(rows)
    detail["flag_tiny_dem_sample_lt_10"] = detail["dem_sample_cells"].fillna(0).lt(10)
    detail["flag_above_allowed_gt_5pct"] = detail["pct_above_reservoir_plus10m"].gt(5)
    detail["flag_low_positive_head_lt_75pct"] = detail["pct_below_reservoir"].lt(75)
    detail["flag_low_allowed_head_lt_95pct"] = detail["pct_below_reservoir_plus10m"].lt(95)
    detail["flag_reservoir_dem_mismatch_gt_100m"] = detail["res_minus_dam_dem_m"].abs().gt(100)
    flag_cols = [col for col in detail.columns if col.startswith("flag_")]
    detail["major_flag_count"] = detail[flag_cols].sum(axis=1).astype(int)
    detail["any_major_flag"] = detail["major_flag_count"].gt(0)

    flagged = detail[detail["any_major_flag"]].copy()
    summary = _build_summary(detail, year)
    return detail, flagged, summary


def _summary_row(detail: pd.DataFrame, label: str) -> dict:
    return {
        "scope": label,
        "n_command_areas": int(len(detail)),
        "n_with_dem_samples": int(detail["dem_sample_cells"].fillna(0).gt(0).sum()),
        "median_pct_below_reservoir": float(detail["pct_below_reservoir"].median()),
        "median_pct_below_reservoir_plus10m": float(detail["pct_below_reservoir_plus10m"].median()),
        "median_pct_above_reservoir_plus10m": float(detail["pct_above_reservoir_plus10m"].median()),
        "p95_pct_above_reservoir_plus10m": float(detail["pct_above_reservoir_plus10m"].quantile(0.95)),
        "median_head_m": float(detail["head_median_m"].median()),
        "median_dam_reservoir_dem_difference_m": float(detail["res_minus_dam_dem_m"].median()),
        "n_tiny_dem_sample_lt_10": int(detail["flag_tiny_dem_sample_lt_10"].sum()),
        "n_above_allowed_gt_5pct": int(detail["flag_above_allowed_gt_5pct"].sum()),
        "n_low_positive_head_lt_75pct": int(detail["flag_low_positive_head_lt_75pct"].sum()),
        "n_low_allowed_head_lt_95pct": int(detail["flag_low_allowed_head_lt_95pct"].sum()),
        "n_reservoir_dem_mismatch_gt_100m": int(detail["flag_reservoir_dem_mismatch_gt_100m"].sum()),
        "n_any_major_flag": int(detail["any_major_flag"].sum()),
    }


def _build_summary(detail: pd.DataFrame, year: int) -> pd.DataFrame:
    rows = [_summary_row(detail, "all_source_command_areas")]
    active = detail[detail["active_by_year"]].copy()
    if not active.empty:
        rows.append(_summary_row(active, f"active_by_{year}"))
    return pd.DataFrame(rows)


def _write_manifest_rows(rows: list[dict]) -> None:
    manifest_path = paper_dir("Paper1_diagnostics_dir") / "paper1_manuscript_asset_manifest.csv"
    if manifest_path.exists():
        manifest = pd.read_csv(manifest_path)
        manifest = manifest[~manifest["asset_name"].isin({row["asset_name"] for row in rows})]
        manifest = pd.concat([manifest, pd.DataFrame(rows)], ignore_index=True)
    else:
        manifest = pd.DataFrame(rows)
    manifest.to_csv(manifest_path, index=False)


def _plot_validation(detail: pd.DataFrame, summary: pd.DataFrame) -> list[dict]:
    figures_dir = paper_dir("Paper1_figures_dir")
    assets: list[dict] = []
    active = detail[detail["active_by_year"]].copy()
    plot_df = active if not active.empty else detail

    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.8))
    axes[0].hist(plot_df["pct_below_reservoir"].dropna(), bins=np.linspace(0, 100, 21), color="#277C78", alpha=0.85)
    axes[0].axvline(75, color="#B33A3A", linestyle="--", linewidth=1)
    axes[0].set_xlabel("Command-area cells below reservoir elevation (%)")
    axes[0].set_ylabel("Command areas")
    axes[0].set_title("Positive-head check")
    axes[0].grid(axis="y", color="#D9D9D9", linewidth=0.8)

    axes[1].hist(plot_df["pct_above_reservoir_plus10m"].dropna(), bins=np.linspace(0, 100, 21), color="#C26A2E", alpha=0.85)
    axes[1].axvline(5, color="#B33A3A", linestyle="--", linewidth=1)
    axes[1].set_xlabel("Cells above reservoir + 10 m (%)")
    axes[1].set_title("Allowed-threshold check")
    axes[1].grid(axis="y", color="#D9D9D9", linewidth=0.8)
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
    path = figures_dir / "figure_6_dem_plausibility_head_checks.png"
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()
    assets.append({"asset_type": "figure_png", "asset_name": "figure_6_dem_plausibility_head_checks", "path": str(path)})

    scatter = plot_df.dropna(subset=["dam_dem_median_3x3_m", "res_elev_m"]).copy()
    fig, ax = plt.subplots(figsize=(5.2, 5.0))
    colors = np.where(scatter["flag_reservoir_dem_mismatch_gt_100m"], "#B33A3A", "#277C78")
    ax.scatter(scatter["dam_dem_median_3x3_m"], scatter["res_elev_m"], s=24, color=colors, alpha=0.75)
    if not scatter.empty:
        lo = float(min(scatter["dam_dem_median_3x3_m"].min(), scatter["res_elev_m"].min()))
        hi = float(max(scatter["dam_dem_median_3x3_m"].max(), scatter["res_elev_m"].max()))
        ax.plot([lo, hi], [lo, hi], color="#666666", linewidth=1, linestyle=":")
    ax.set_xlabel("Local DEM elevation at dam point, median 3x3 (m)")
    ax.set_ylabel("Exported reservoir elevation (m)")
    ax.set_title("Reservoir elevation metadata sanity check")
    ax.grid(color="#D9D9D9", linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    path = figures_dir / "figure_7_reservoir_dem_sanity_check.png"
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()
    assets.append({"asset_type": "figure_png", "asset_name": "figure_7_reservoir_dem_sanity_check", "path": str(path)})

    tables_dir = paper_dir("Paper1_tables_dir")
    summary_table_path = tables_dir / "table_5_dem_plausibility_summary.csv"
    summary.to_csv(summary_table_path, index=False)
    assets.append({"asset_type": "table_csv", "asset_name": "table_5_dem_plausibility_summary", "path": str(summary_table_path)})

    return assets


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-resolution-m", type=float, default=DEFAULT_TARGET_RESOLUTION_M)
    parser.add_argument("--year", type=int, default=END_YEAR, help="Year used to mark command areas active/inactive.")
    args = parser.parse_args(argv)

    ensure_paper_dirs()
    detail, flagged, summary = _validate(args.target_resolution_m, args.year)

    detail_path = final_tables_dir() / DETAIL_TABLE
    summary_path = final_tables_dir() / SUMMARY_TABLE
    flagged_path = paper_dir("Paper1_diagnostics_dir") / FLAGGED_TABLE
    detail.to_csv(detail_path, index=False)
    summary.to_csv(summary_path, index=False)
    flagged.to_csv(flagged_path, index=False)

    manifest_rows = [
        {"asset_type": "final_table_csv", "asset_name": "paper1_command_area_dem_plausibility_by_dam", "path": str(detail_path)},
        {"asset_type": "final_table_csv", "asset_name": "paper1_command_area_dem_plausibility_summary", "path": str(summary_path)},
        {"asset_type": "diagnostic_csv", "asset_name": "paper1_command_area_dem_plausibility_flagged", "path": str(flagged_path)},
    ]
    manifest_rows.extend(_plot_validation(detail, summary))
    _write_manifest_rows(manifest_rows)

    print(f"Wrote DEM plausibility detail table: {detail_path}")
    print(f"Wrote DEM plausibility summary: {summary_path}")
    print(f"Wrote flagged command-area diagnostics: {flagged_path}")
    print(summary.round(3).to_string(index=False))
    if not flagged.empty:
        cols = [
            "GDW_ID",
            "active_by_year",
            "pct_below_reservoir",
            "pct_below_reservoir_plus10m",
            "pct_above_reservoir_plus10m",
            "res_minus_dam_dem_m",
            "major_flag_count",
        ]
        print("\nFlagged command areas:")
        print(flagged[cols].round(3).head(20).to_string(index=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except WorkflowInputError as exc:
        raise SystemExit(f"ERROR: {exc}") from None
