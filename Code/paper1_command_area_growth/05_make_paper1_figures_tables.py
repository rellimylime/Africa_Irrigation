"""Build manuscript-ready Paper 1 figures and tables.

This script consumes the checked CSV outputs from steps 03 and 04. It does not
change the analytical results; it only formats the primary area-weighted result,
the extraction-sensitivity checks, and the command-area QA into reusable paper
assets.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", str(Path(os.environ.get("TMP", "C:/tmp")) / "paper1_matplotlib"))

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from paper1_common import (  # noqa: E402
    AFRICA_EQUAL_AREA_CRS,
    COMMAND_AREA_LAYER,
    WorkflowInputError,
    config_path,
    ensure_paper_dirs,
    final_tables_dir,
    paper_dir,
    yearly_command_area_path,
)


BASE_YEAR = 2000
END_YEAR = 2015
PRIMARY_TAG = "area_weighted"

TABLE_HEADLINE = "table_1_headline_summary"
TABLE_SENSITIVITY = "table_2_extraction_sensitivity"
TABLE_COUNTRIES = "table_3_top_country_growth_contributors"
TABLE_YEARLY = "table_4_yearly_inside_outside_totals"
OUTPUT_MANIFEST = "paper1_manuscript_asset_manifest.csv"


def _tagged_csv_path(path: Path, output_tag: str | None) -> Path:
    if output_tag is None:
        return path
    tag = output_tag.strip().replace("-", "_")
    if not tag or not tag.replace("_", "").isalnum():
        raise WorkflowInputError(f"Invalid output tag: {output_tag!r}")
    return path.with_name(f"{path.stem}_{tag}{path.suffix}")


def _read_csv(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        raise WorkflowInputError(f"Missing {label}: {path}")
    return pd.read_csv(path)


def _metric_value(qa: pd.DataFrame, metric: str, default: str | float | int | None = None):
    if "metric" not in qa.columns or "value" not in qa.columns:
        return default
    matches = qa.loc[qa["metric"].eq(metric), "value"]
    if matches.empty:
        return default
    return matches.iloc[0]


def _as_float(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return np.nan


def _pct(value: float) -> float:
    return float(value) * 100 if pd.notna(value) else np.nan


def _round_numeric(df: pd.DataFrame, digits: int = 3) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_numeric_dtype(out[col]):
            out[col] = out[col].round(digits)
    return out


def _markdown_table(df: pd.DataFrame) -> str:
    display = df.fillna("").astype(str)
    columns = list(display.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for _, row in display.iterrows():
        lines.append("| " + " | ".join(row[col] for col in columns) + " |")
    return "\n".join(lines) + "\n"


def _write_table(df: pd.DataFrame, name: str, tables_dir: Path, manifest_rows: list[dict]) -> tuple[Path, Path]:
    csv_path = tables_dir / f"{name}.csv"
    md_path = tables_dir / f"{name}.md"
    df.to_csv(csv_path, index=False)
    md_path.write_text(_markdown_table(_round_numeric(df)), encoding="utf-8")
    manifest_rows.extend(
        [
            {"asset_type": "table_csv", "asset_name": name, "path": str(csv_path)},
            {"asset_type": "table_markdown", "asset_name": name, "path": str(md_path)},
        ]
    )
    return csv_path, md_path


def _savefig(path: Path, manifest_rows: list[dict], asset_name: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()
    manifest_rows.append({"asset_type": "figure_png", "asset_name": asset_name, "path": str(path)})


def _load_inputs() -> dict[str, pd.DataFrame]:
    primary_panel_path = _tagged_csv_path(config_path("Paper1_inside_outside_panel_csv_path"), PRIMARY_TAG)
    primary_country_path = _tagged_csv_path(config_path("Paper1_growth_decomposition_csv_path"), PRIMARY_TAG)
    sensitivity_path = final_tables_dir() / "paper1_extraction_sensitivity_summary.csv"
    qa_path = final_tables_dir() / "paper1_input_qa_summary.csv"
    yearly_qa_path = final_tables_dir() / "paper1_yearly_command_area_qa.csv"

    return {
        "panel": _read_csv(primary_panel_path, "primary area-weighted inside/outside panel"),
        "country": _read_csv(primary_country_path, "primary area-weighted country growth table"),
        "sensitivity": _read_csv(sensitivity_path, "extraction sensitivity summary"),
        "qa": _read_csv(qa_path, "input QA summary"),
        "yearly_qa": _read_csv(yearly_qa_path, "yearly command-area QA"),
    }


def _build_headline_table(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    sensitivity = data["sensitivity"].copy()
    qa = data["qa"]
    yearly_qa = data["yearly_qa"]

    primary = sensitivity[sensitivity["variant"].eq(PRIMARY_TAG)]
    if primary.empty:
        raise WorkflowInputError(f"Sensitivity summary has no primary variant named {PRIMARY_TAG!r}.")
    primary_row = primary.iloc[0]

    share_min = _pct(pd.to_numeric(sensitivity["outside_growth_share"], errors="coerce").min())
    share_max = _pct(pd.to_numeric(sensitivity["outside_growth_share"], errors="coerce").max())
    active_2015 = yearly_qa.loc[yearly_qa["year"].eq(END_YEAR), "n_unique_dams"]
    active_2015_value = int(active_2015.iloc[0]) if not active_2015.empty else pd.NA

    rows = [
        {"metric": "Primary extraction method", "value": "Area-weighted fractional raster-cell overlap"},
        {"metric": "Study period", "value": f"{BASE_YEAR}-{END_YEAR}"},
        {"metric": "Panel countries", "value": int(primary_row["n_countries"])},
        {
            "metric": "Total AEI growth, ha",
            "value": round(float(primary_row["total_growth_ha"]), 1),
        },
        {
            "metric": "Growth inside large-dam command areas, ha",
            "value": round(float(primary_row["inside_growth_ha"]), 1),
        },
        {
            "metric": "Growth outside large-dam command areas, ha",
            "value": round(float(primary_row["outside_growth_ha"]), 1),
        },
        {
            "metric": "Growth outside large-dam command areas, percent",
            "value": round(_pct(float(primary_row["outside_growth_share"])), 2),
        },
        {
            "metric": "Sensitivity range, outside-growth percent",
            "value": f"{share_min:.2f}-{share_max:.2f}",
        },
        {
            "metric": "Valid physical-envelope command-area polygons",
            "value": int(_as_float(_metric_value(qa, "command_area_features", np.nan))),
        },
        {
            "metric": "2015 active command-area dams",
            "value": active_2015_value,
        },
        {
            "metric": "2015 active command-area area, ha",
            "value": round(
                float(yearly_qa.loc[yearly_qa["year"].eq(END_YEAR), "command_area_ha"].iloc[0]),
                1,
            )
            if not yearly_qa.loc[yearly_qa["year"].eq(END_YEAR)].empty
            else pd.NA,
        },
    ]
    return pd.DataFrame(rows)


def _build_sensitivity_table(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    sensitivity = data["sensitivity"].copy()
    out = sensitivity[
        [
            "variant",
            "variant_label",
            "is_primary",
            "inside_growth_ha",
            "outside_growth_ha",
            "total_growth_ha",
            "outside_growth_share",
            "outside_share_base",
            "outside_share_end",
        ]
    ].copy()
    out["outside_growth_share_pct"] = out["outside_growth_share"].map(_pct)
    out["outside_share_2000_pct"] = out["outside_share_base"].map(_pct)
    out["outside_share_2015_pct"] = out["outside_share_end"].map(_pct)
    out = out.drop(columns=["outside_growth_share", "outside_share_base", "outside_share_end"])
    return out.sort_values(["is_primary", "variant"], ascending=[False, True])


def _build_country_table(data: dict[str, pd.DataFrame], n: int = 15) -> pd.DataFrame:
    country = data["country"].copy()
    country["total_growth_ha"] = pd.to_numeric(country["total_growth_ha"], errors="coerce")
    country["inside_growth_ha"] = pd.to_numeric(country["inside_growth_ha"], errors="coerce")
    country["outside_growth_ha"] = pd.to_numeric(country["outside_growth_ha"], errors="coerce")
    country["outside_growth_share_pct"] = pd.to_numeric(country["outside_growth_share"], errors="coerce").map(_pct)
    country["outside_share_2015_pct"] = pd.to_numeric(country["outside_share_end"], errors="coerce").map(_pct)

    out = country[country["total_growth_ha"].gt(0)].copy()
    out = out.sort_values("total_growth_ha", ascending=False).head(n)
    return out[
        [
            "ISO",
            "country_name",
            "inside_growth_ha",
            "outside_growth_ha",
            "total_growth_ha",
            "outside_growth_share_pct",
            "outside_share_2015_pct",
        ]
    ]


def _build_yearly_table(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    panel = data["panel"].copy()
    value_cols = ["inside_AEI_ha", "outside_AEI_ha", "total_AEI_ha"]
    for col in value_cols:
        panel[col] = pd.to_numeric(panel[col], errors="coerce").fillna(0.0)
    yearly = panel.groupby("year", as_index=False)[value_cols].sum()
    yearly["inside_share_pct"] = np.where(yearly["total_AEI_ha"].ne(0), yearly["inside_AEI_ha"] / yearly["total_AEI_ha"] * 100, np.nan)
    yearly["outside_share_pct"] = np.where(yearly["total_AEI_ha"].ne(0), yearly["outside_AEI_ha"] / yearly["total_AEI_ha"] * 100, np.nan)

    qa = data["yearly_qa"][["year", "n_unique_dams", "command_area_ha"]].copy()
    yearly = yearly.merge(qa, on="year", how="left")
    return yearly


def _figure_growth_decomposition(sensitivity: pd.DataFrame, figures_dir: Path, manifest_rows: list[dict]) -> None:
    primary = sensitivity[sensitivity["variant"].eq(PRIMARY_TAG)].iloc[0]
    values = np.array([primary["inside_growth_ha"], primary["outside_growth_ha"]], dtype=float) / 1000
    shares = np.array([primary["inside_growth_share"], primary["outside_growth_share"]], dtype=float) * 100
    labels = ["Inside command areas", "Outside command areas"]
    colors = ["#277C78", "#C26A2E"]

    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    y = np.arange(len(labels))
    bars = ax.barh(y, values, color=colors, height=0.55)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlabel("AEI growth, 2000-2015 (thousand ha)")
    ax.set_title("Most AEI growth is outside large-dam command-area envelopes")
    ax.grid(axis="x", color="#D9D9D9", linewidth=0.8)
    ax.set_axisbelow(True)
    for bar, value, share in zip(bars, values, shares):
        ax.text(
            bar.get_width() + values.max() * 0.025,
            bar.get_y() + bar.get_height() / 2,
            f"{value:,.1f}k ha ({share:.1f}%)",
            va="center",
            fontsize=10,
        )
    ax.spines[["top", "right", "left"]].set_visible(False)
    _savefig(figures_dir / "figure_1_growth_decomposition.png", manifest_rows, "figure_1_growth_decomposition")


def _figure_sensitivity(sensitivity: pd.DataFrame, figures_dir: Path, manifest_rows: list[dict]) -> None:
    df = sensitivity.copy()
    df["outside_growth_share_pct"] = pd.to_numeric(df["outside_growth_share"], errors="coerce") * 100
    order = ["area_weighted", "center_cell", "all_touched"]
    df["order"] = df["variant"].map({name: i for i, name in enumerate(order)}).fillna(99)
    df = df.sort_values("order")

    fig, ax = plt.subplots(figsize=(7.0, 3.8))
    x = np.arange(len(df))
    colors = np.where(df["is_primary"].astype(str).str.lower().isin({"true", "1"}), "#277C78", "#8E8E8E")
    ax.scatter(x, df["outside_growth_share_pct"], s=90, color=colors, zorder=3)
    ax.plot(x, df["outside_growth_share_pct"], color="#B6B6B6", linewidth=1.2, zorder=2)
    ax.set_xticks(x, df["variant_label"], rotation=15, ha="right")
    ymin = max(0, df["outside_growth_share_pct"].min() - 0.4)
    ymax = min(100, df["outside_growth_share_pct"].max() + 0.4)
    ax.set_ylim(ymin, ymax)
    ax.set_ylabel("Outside-command-area growth share (%)")
    ax.set_title("Headline is robust to extraction method")
    ax.grid(axis="y", color="#D9D9D9", linewidth=0.8)
    for xi, yi in zip(x, df["outside_growth_share_pct"]):
        ax.text(xi, yi + 0.08, f"{yi:.1f}%", ha="center", va="bottom", fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    _savefig(figures_dir / "figure_2_extraction_sensitivity.png", manifest_rows, "figure_2_extraction_sensitivity")


def _figure_timeseries(yearly: pd.DataFrame, figures_dir: Path, manifest_rows: list[dict]) -> None:
    df = yearly.sort_values("year").copy()
    fig, axes = plt.subplots(2, 1, figsize=(7.2, 5.2), sharex=True, gridspec_kw={"height_ratios": [2, 1]})

    axes[0].plot(df["year"], df["total_AEI_ha"] / 1e6, marker="o", color="#333333", label="Total")
    axes[0].plot(df["year"], df["outside_AEI_ha"] / 1e6, marker="o", color="#C26A2E", label="Outside")
    axes[0].set_ylabel("AEI area (million ha)")
    axes[0].set_title("AEI area inside and outside active command areas")
    axes[0].grid(axis="y", color="#D9D9D9", linewidth=0.8)
    axes[0].legend(frameon=False, loc="upper left")

    axes[1].plot(df["year"], df["inside_AEI_ha"] / 1000, marker="o", color="#277C78")
    axes[1].set_ylabel("Inside area\n(thousand ha)")
    axes[1].set_xlabel("Year")
    axes[1].grid(axis="y", color="#D9D9D9", linewidth=0.8)

    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
    _savefig(figures_dir / "figure_3_inside_outside_timeseries.png", manifest_rows, "figure_3_inside_outside_timeseries")


def _figure_top_countries(country_table: pd.DataFrame, figures_dir: Path, manifest_rows: list[dict]) -> None:
    df = country_table.head(12).sort_values("total_growth_ha", ascending=True).copy()
    inside = df["inside_growth_ha"].clip(lower=0) / 1000
    outside = df["outside_growth_ha"].clip(lower=0) / 1000

    fig, ax = plt.subplots(figsize=(7.5, 5.0))
    ax.barh(df["country_name"], outside, color="#C26A2E", label="Outside")
    ax.barh(df["country_name"], inside, left=outside, color="#277C78", label="Inside")
    ax.set_xlabel("Positive AEI growth, 2000-2015 (thousand ha)")
    ax.set_title("Largest country contributors to AEI growth")
    ax.grid(axis="x", color="#D9D9D9", linewidth=0.8)
    ax.legend(frameon=False, loc="lower right")
    ax.spines[["top", "right", "left"]].set_visible(False)
    _savefig(figures_dir / "figure_4_top_country_growth_contributors.png", manifest_rows, "figure_4_top_country_growth_contributors")


def _figure_command_area_map(figures_dir: Path, manifest_rows: list[dict]) -> None:
    study = gpd.read_file(config_path("SSA_All_by_Country_shp_path")).to_crs(AFRICA_EQUAL_AREA_CRS)
    ca_path = yearly_command_area_path(END_YEAR)
    if not ca_path.exists():
        raise WorkflowInputError(f"Missing {END_YEAR} command-area layer: {ca_path}")
    try:
        command_areas = gpd.read_file(ca_path, layer=COMMAND_AREA_LAYER)
    except ValueError:
        command_areas = gpd.read_file(ca_path)
    command_areas = command_areas.to_crs(AFRICA_EQUAL_AREA_CRS)

    dams = gpd.read_file(config_path("GDW_Arid_SSA_Final_Irr_shp_path")).to_crs(AFRICA_EQUAL_AREA_CRS)
    if "DAM_HGT_M" in dams.columns:
        dams["DAM_HGT_M_NUM"] = pd.to_numeric(dams["DAM_HGT_M"], errors="coerce")
        dams = dams[dams["DAM_HGT_M_NUM"].gt(15)]

    fig, ax = plt.subplots(figsize=(7.2, 7.2))
    study.plot(ax=ax, facecolor="#F2EFE8", edgecolor="#B9B3A8", linewidth=0.45)
    command_areas.plot(ax=ax, color="#277C78", alpha=0.78, edgecolor="none")
    if not dams.empty:
        dams.plot(ax=ax, color="#303030", markersize=5, alpha=0.65)
    ax.set_title("Active large-dam command-area envelopes in 2015")
    ax.set_axis_off()
    ax.legend(
        handles=[
            Line2D([0], [0], marker="s", color="none", markerfacecolor="#F2EFE8", markeredgecolor="#B9B3A8", markersize=10, label="Arid SSA study mask"),
            Line2D([0], [0], marker="s", color="none", markerfacecolor="#277C78", markersize=10, label="2015 command areas"),
            Line2D([0], [0], marker="o", color="none", markerfacecolor="#303030", markersize=5, label="Irrigation dams >15 m"),
        ],
        frameon=False,
        loc="lower left",
    )
    _savefig(figures_dir / "figure_5_command_area_map_2015.png", manifest_rows, "figure_5_command_area_map_2015")


def main() -> int:
    ensure_paper_dirs()
    figures_dir = paper_dir("Paper1_figures_dir")
    tables_dir = paper_dir("Paper1_tables_dir")
    diagnostics_dir = paper_dir("Paper1_diagnostics_dir")
    manifest_rows: list[dict] = []

    data = _load_inputs()
    headline = _build_headline_table(data)
    sensitivity_table = _build_sensitivity_table(data)
    country_table = _build_country_table(data)
    yearly_table = _build_yearly_table(data)

    _write_table(headline, TABLE_HEADLINE, tables_dir, manifest_rows)
    _write_table(sensitivity_table, TABLE_SENSITIVITY, tables_dir, manifest_rows)
    _write_table(country_table, TABLE_COUNTRIES, tables_dir, manifest_rows)
    _write_table(yearly_table, TABLE_YEARLY, tables_dir, manifest_rows)

    _figure_growth_decomposition(data["sensitivity"], figures_dir, manifest_rows)
    _figure_sensitivity(data["sensitivity"], figures_dir, manifest_rows)
    _figure_timeseries(yearly_table, figures_dir, manifest_rows)
    _figure_top_countries(country_table, figures_dir, manifest_rows)
    _figure_command_area_map(figures_dir, manifest_rows)

    manifest = pd.DataFrame(manifest_rows)
    manifest_path = diagnostics_dir / OUTPUT_MANIFEST
    manifest.to_csv(manifest_path, index=False)
    print(f"Wrote manuscript asset manifest: {manifest_path}")
    print(manifest.to_string(index=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except WorkflowInputError as exc:
        raise SystemExit(f"ERROR: {exc}") from None
