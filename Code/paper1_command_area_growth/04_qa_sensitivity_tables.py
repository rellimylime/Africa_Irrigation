"""Build Paper 1 QA and extraction-sensitivity tables.

This script preserves variant outputs instead of overwriting the canonical
inside/outside panel. It writes compact CSVs that document input sanity checks
and the robustness of the 2000-2015 growth decomposition to extraction method.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from paper1_common import (
    AFRICA_EQUAL_AREA_CRS,
    EXTRACTION_DIAGNOSTICS,
    YEARLY_COMMAND_AREA_INVENTORY,
    WorkflowInputError,
    config_path,
    ensure_paper_dirs,
    extracted_irrigation_dir,
    final_tables_dir,
    find_vector_path,
)


BASE_YEAR = 2000
END_YEAR = 2015
PRIMARY_TAG = "area_weighted"
VARIANTS = [
    {
        "tag": "area_weighted",
        "label": "Area-weighted fractional overlap",
        "extract_args": ["--area-weighted"],
        "primary": True,
    },
    {
        "tag": "all_touched",
        "label": "Binary raster mask, all touched cells",
        "extract_args": ["--all-touched"],
        "primary": False,
    },
    {
        "tag": "center_cell",
        "label": "Binary raster mask, cell center",
        "extract_args": [],
        "primary": False,
    },
]


def _tagged_csv_path(path: Path, output_tag: str | None) -> Path:
    if output_tag is None:
        return path
    tag = output_tag.strip().replace("-", "_")
    if not tag or not tag.replace("_", "").isalnum():
        raise WorkflowInputError(
            f"Output tag must use only letters, numbers, underscores, or hyphens: {output_tag!r}"
        )
    return path.with_name(f"{path.stem}_{tag}{path.suffix}")


def _panel_path(tag: str | None = None) -> Path:
    return _tagged_csv_path(config_path("Paper1_inside_outside_panel_csv_path"), tag)


def _diagnostics_path(tag: str | None = None) -> Path:
    return _tagged_csv_path(extracted_irrigation_dir() / EXTRACTION_DIAGNOSTICS, tag)


def _growth_country_path(tag: str | None = None) -> Path:
    return _tagged_csv_path(config_path("Paper1_growth_decomposition_csv_path"), tag)


def _growth_summary_path(tag: str | None = None) -> Path:
    return _tagged_csv_path(config_path("Paper1_growth_summary_csv_path"), tag)


def _run_python(args: list[str]) -> None:
    cmd = [sys.executable, *args]
    print("Running:", " ".join(str(part) for part in cmd), flush=True)
    subprocess.run(cmd, cwd=Path(__file__).resolve().parents[2], check=True)


def _copy_canonical_area_weighted_if_current() -> bool:
    """Copy the current canonical panel to the area-weighted variant if it matches."""

    panel = _panel_path(None)
    diagnostics = _diagnostics_path(None)
    tagged_panel = _panel_path(PRIMARY_TAG)
    tagged_diagnostics = _diagnostics_path(PRIMARY_TAG)
    if not panel.exists() or not diagnostics.exists():
        return False

    diag = pd.read_csv(diagnostics)
    method_values = set(diag.get("extraction_method", pd.Series(dtype=str)).dropna().astype(str))
    if method_values != {"area_weighted"}:
        return False

    tagged_panel.parent.mkdir(parents=True, exist_ok=True)
    tagged_diagnostics.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(panel, tagged_panel)
    shutil.copy2(diagnostics, tagged_diagnostics)
    print(f"Copied canonical area-weighted panel to variant output: {tagged_panel}", flush=True)
    return True


def _ensure_variant_outputs(variant: dict, rerun: bool) -> None:
    tag = variant["tag"]
    panel_path = _panel_path(tag)
    diagnostics_path = _diagnostics_path(tag)

    if tag == PRIMARY_TAG and not rerun and (not panel_path.exists() or not diagnostics_path.exists()):
        _copy_canonical_area_weighted_if_current()

    if rerun or not panel_path.exists() or not diagnostics_path.exists():
        _run_python(
            [
                str(SCRIPT_DIR / "02_extract_irrigation_inside_outside.py"),
                *variant["extract_args"],
                "--output-tag",
                tag,
            ]
        )

    _run_python(
        [
            str(SCRIPT_DIR / "03_growth_decomposition.py"),
            "--base-year",
            str(BASE_YEAR),
            "--end-year",
            str(END_YEAR),
            "--output-tag",
            tag,
        ]
    )


def _write_input_qa_tables() -> tuple[Path, Path]:
    ca_source = find_vector_path("No_Crop_Vectorized_Command_Area_shp_path")
    ca = gpd.read_file(ca_source.path)
    ca_area_ha = np.nan
    if ca.crs is not None and not ca.empty:
        ca_area_ha = float(ca.to_crs(AFRICA_EQUAL_AREA_CRS).geometry.area.sum() / 10_000)
    elif "area" in ca.columns:
        ca_area_ha = float(pd.to_numeric(ca["area"], errors="coerce").sum() / 10_000)

    gdw = gpd.read_file(config_path("GDW_Arid_SSA_Final_Irr_shp_path"))
    inventory_path = final_tables_dir() / YEARLY_COMMAND_AREA_INVENTORY
    if not inventory_path.exists():
        raise WorkflowInputError(f"Missing yearly command-area inventory: {inventory_path}")
    inventory = pd.read_csv(inventory_path)

    type_values = ", ".join(sorted(ca["type"].dropna().astype(str).unique())) if "type" in ca.columns else ""
    valid_count = int(ca["validCA"].astype(str).str.lower().isin({"true", "1", "t", "yes"}).sum()) if "validCA" in ca.columns else pd.NA
    source_years = pd.to_numeric(ca["YEAR_DAM"], errors="coerce") if "YEAR_DAM" in ca.columns else pd.Series(dtype=float)

    summary_rows = [
        {"metric": "command_area_source_path", "value": str(ca_source.path), "note": ca_source.note},
        {"metric": "command_area_features", "value": int(len(ca)), "note": ""},
        {"metric": "command_area_unique_gdw_ids", "value": int(ca["GDW_ID"].nunique()) if "GDW_ID" in ca.columns else pd.NA, "note": ""},
        {"metric": "command_area_validCA_true", "value": valid_count, "note": ""},
        {"metric": "command_area_type_values", "value": type_values, "note": ""},
        {"metric": "command_area_area_ha_equal_area", "value": ca_area_ha, "note": "Computed in Africa equal-area CRS."},
        {"metric": "gdw_irrigation_dams_features", "value": int(len(gdw)), "note": "Processed any-use irrigation dams >15 m."},
        {
            "metric": "command_area_export_year_missing",
            "value": int(source_years.isin([-99, -999, -9999, 0]).sum()) if not source_years.empty else pd.NA,
            "note": "From YEAR_DAM in the raw command-area export.",
        },
        {
            "metric": "command_area_export_year_after_2015",
            "value": int((source_years > END_YEAR).sum()) if not source_years.empty else pd.NA,
            "note": "These command areas are valid source features but inactive for the 2000-2015 headline.",
        },
    ]
    summary = pd.DataFrame(summary_rows)

    yearly_cols = [
        "year",
        "n_source_polygons",
        "n_unique_dams",
        "dam_year_min",
        "dam_year_max",
        "raw_command_area_ha",
        "command_area_ha",
        "overlap_area_ha",
        "overlap_pct_of_raw",
        "status",
        "source_path",
    ]
    yearly = inventory[[col for col in yearly_cols if col in inventory.columns]].copy()

    summary_path = final_tables_dir() / "paper1_input_qa_summary.csv"
    yearly_path = final_tables_dir() / "paper1_yearly_command_area_qa.csv"
    summary.to_csv(summary_path, index=False)
    yearly.to_csv(yearly_path, index=False)
    print(f"Wrote input QA summary: {summary_path}", flush=True)
    print(f"Wrote yearly command-area QA: {yearly_path}", flush=True)
    return summary_path, yearly_path


def _write_sensitivity_summary() -> Path:
    rows = []
    for variant in VARIANTS:
        tag = variant["tag"]
        summary_path = _growth_summary_path(tag)
        diagnostics_path = _diagnostics_path(tag)
        if not summary_path.exists():
            raise WorkflowInputError(f"Missing growth summary for {tag}: {summary_path}")
        summary = pd.read_csv(summary_path)
        if len(summary) != 1:
            raise WorkflowInputError(f"Expected one summary row for {tag}, found {len(summary)}")
        row = summary.iloc[0].to_dict()
        diagnostics = pd.read_csv(diagnostics_path) if diagnostics_path.exists() else pd.DataFrame()
        row.update(
            {
                "variant": tag,
                "variant_label": variant["label"],
                "is_primary": bool(variant["primary"]),
                "extraction_method": (
                    ", ".join(sorted(diagnostics["extraction_method"].dropna().astype(str).unique()))
                    if "extraction_method" in diagnostics.columns
                    else ""
                ),
                "all_touched": (
                    ", ".join(sorted(diagnostics["all_touched"].dropna().astype(str).unique()))
                    if "all_touched" in diagnostics.columns
                    else ""
                ),
                "panel_path": str(_panel_path(tag)),
                "growth_summary_path": str(summary_path),
            }
        )
        rows.append(row)

    out = pd.DataFrame(rows)
    leading = ["variant", "variant_label", "is_primary", "extraction_method", "all_touched"]
    out = out[leading + [col for col in out.columns if col not in leading]]
    out_path = final_tables_dir() / "paper1_extraction_sensitivity_summary.csv"
    out.to_csv(out_path, index=False)
    print(f"Wrote extraction sensitivity summary: {out_path}", flush=True)
    print(
        out[
            [
                "variant",
                "total_growth_ha",
                "inside_growth_ha",
                "outside_growth_ha",
                "outside_growth_share",
            ]
        ].round(3).to_string(index=False),
        flush=True,
    )
    return out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rerun", action="store_true", help="Rerun all extraction variants even if tagged outputs exist.")
    args = parser.parse_args(argv)

    ensure_paper_dirs()
    _write_input_qa_tables()
    for variant in VARIANTS:
        _ensure_variant_outputs(variant, rerun=args.rerun)
    _write_sensitivity_summary()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except WorkflowInputError as exc:
        raise SystemExit(f"ERROR: {exc}") from None
