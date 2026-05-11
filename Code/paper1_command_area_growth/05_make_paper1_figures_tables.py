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

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Circle, Rectangle

plt.rcParams.update(
    {
        "font.size": 9,
        "axes.titlesize": 11,
        "axes.labelsize": 9,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "figure.titlesize": 12,
    }
)


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from paper1_common import (  # noqa: E402
    WorkflowInputError,
    config_path,
    ensure_paper_dirs,
    final_tables_dir,
    paper_dir,
)


BASE_YEAR = 2000
END_YEAR = 2015
PRIMARY_TAG = "area_weighted"

TABLE_HEADLINE = "table_1_headline_summary"
TABLE_SENSITIVITY = "table_2_extraction_sensitivity"
TABLE_COUNTRIES = "table_3_top_country_growth_contributors"
TABLE_YEARLY = "table_4_yearly_inside_outside_totals"
TABLE_CONTRIBUTION = "table_7_standardized_growth_contribution"
TABLE_CONCENTRATION = "table_8_country_concentration_checks"
TABLE_COHORT = "table_9_dam_cohort_growth_context"
OUTPUT_MANIFEST = "paper1_manuscript_asset_manifest.csv"
DEPRECATED_FIGURES = ("figure_5_command_area_map_2015.png",)
DEPRECATED_ASSET_NAMES = ("figure_5_command_area_map_2015",)


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


def _remove_deprecated_assets(figures_dir: Path) -> None:
    for name in DEPRECATED_FIGURES:
        path = figures_dir / name
        if path.exists():
            path.unlink()


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


def _build_contribution_table(sensitivity: pd.DataFrame, yearly: pd.DataFrame) -> pd.DataFrame:
    primary = sensitivity[sensitivity["variant"].eq(PRIMARY_TAG)]
    if primary.empty:
        raise WorkflowInputError(f"Sensitivity summary has no primary variant named {PRIMARY_TAG!r}.")
    primary_row = primary.iloc[0]
    base = yearly.loc[yearly["year"].eq(BASE_YEAR)].iloc[0]
    end = yearly.loc[yearly["year"].eq(END_YEAR)].iloc[0]

    total_growth = float(primary_row["total_growth_ha"])
    inside_growth = float(primary_row["inside_growth_ha"])
    outside_growth = float(primary_row["outside_growth_ha"])
    base_total = float(base["total_AEI_ha"])
    base_ca = float(base["command_area_ha"])
    end_ca = float(end["command_area_ha"])

    return pd.DataFrame(
        [
            {
                "inside_growth_ha": inside_growth,
                "outside_growth_ha": outside_growth,
                "total_growth_ha": total_growth,
                "inside_share_of_total_growth_pct": inside_growth / total_growth * 100 if total_growth else np.nan,
                "outside_share_of_total_growth_pct": outside_growth / total_growth * 100 if total_growth else np.nan,
                "inside_growth_pct_points_of_2000_total_AEI": inside_growth / base_total * 100 if base_total else np.nan,
                "outside_growth_pct_points_of_2000_total_AEI": outside_growth / base_total * 100 if base_total else np.nan,
                "total_growth_pct_of_2000_total_AEI": total_growth / base_total * 100 if base_total else np.nan,
                "inside_share_of_total_AEI_2000_pct": float(base["inside_share_pct"]),
                "inside_share_of_total_AEI_2015_pct": float(end["inside_share_pct"]),
                "inside_share_change_pct_points": float(end["inside_share_pct"]) - float(base["inside_share_pct"]),
                "inside_AEI_per_command_area_2000_pct": float(base["inside_AEI_ha"]) / base_ca * 100 if base_ca else np.nan,
                "inside_AEI_per_command_area_2015_pct": float(end["inside_AEI_ha"]) / end_ca * 100 if end_ca else np.nan,
                "inside_AEI_per_command_area_change_pct_points": (
                    float(end["inside_AEI_ha"]) / end_ca * 100 - float(base["inside_AEI_ha"]) / base_ca * 100
                    if base_ca and end_ca
                    else np.nan
                ),
                "active_command_area_dams_2000": int(base["n_unique_dams"]),
                "active_command_area_dams_2015": int(end["n_unique_dams"]),
                "new_active_command_area_dams_2001_2015": int(end["n_unique_dams"]) - int(base["n_unique_dams"]),
                "command_area_growth_ha_2001_2015": end_ca - base_ca,
            }
        ]
    )


def _build_concentration_table(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    country = data["country"].copy()
    for col in ("inside_growth_ha", "outside_growth_ha", "total_growth_ha"):
        country[col] = pd.to_numeric(country[col], errors="coerce").fillna(0.0)
    positive = country[country["total_growth_ha"].gt(0)].copy()

    total_growth = country["total_growth_ha"].sum()
    outside_growth = country["outside_growth_ha"].sum()
    inside_growth = country["inside_growth_ha"].sum()
    positive["outside_growth_share_pct"] = positive["outside_growth_ha"] / positive["total_growth_ha"] * 100

    top_total = positive.sort_values("total_growth_ha", ascending=False)
    top_inside = positive.sort_values("inside_growth_ha", ascending=False)
    top_outside = positive.sort_values("outside_growth_ha", ascending=False)

    def share_without(iso: str) -> float:
        subset = country[country["ISO"].ne(iso)]
        return subset["outside_growth_ha"].sum() / subset["total_growth_ha"].sum() * 100

    rows = [
        {"metric": "Countries with positive total AEI growth", "value": len(positive)},
        {
            "metric": "Positive-growth countries with zero inside-envelope growth",
            "value": int((positive["inside_growth_ha"].abs() < 1e-9).sum()),
        },
        {
            "metric": "Positive-growth countries with at least 95% of growth outside envelopes",
            "value": int((positive["outside_growth_share_pct"] >= 95).sum()),
        },
        {
            "metric": "Positive-growth countries with all growth outside envelopes",
            "value": int(np.isclose(positive["outside_growth_share_pct"], 100).sum()),
        },
        {
            "metric": "Top 5 total-growth countries' share of regional net growth (%)",
            "value": top_total.head(5)["total_growth_ha"].sum() / total_growth * 100 if total_growth else np.nan,
        },
        {
            "metric": "Top 8 total-growth countries' share of regional net growth (%)",
            "value": top_total.head(8)["total_growth_ha"].sum() / total_growth * 100 if total_growth else np.nan,
        },
        {
            "metric": "Top 3 outside-growth countries' share of regional outside growth (%)",
            "value": top_outside.head(3)["outside_growth_ha"].sum() / outside_growth * 100 if outside_growth else np.nan,
        },
    ]
    if not top_inside.empty and inside_growth:
        top = top_inside.iloc[0]
        rows.extend(
            [
                {"metric": "Largest inside-growth country", "value": top["country_name"]},
                {"metric": "Largest inside-growth country inside growth (ha)", "value": float(top["inside_growth_ha"])},
                {
                    "metric": "Largest inside-growth country share of regional inside growth (%)",
                    "value": float(top["inside_growth_ha"]) / inside_growth * 100,
                },
            ]
        )
    if "SEN" in set(country["ISO"]):
        rows.append({"metric": "Outside-growth share excluding Senegal (%)", "value": share_without("SEN")})
    if "MLI" in set(country["ISO"]):
        rows.append({"metric": "Outside-growth share excluding Mali (%)", "value": share_without("MLI")})
    return pd.DataFrame(rows)


def _build_dam_cohort_table(yearly: pd.DataFrame) -> pd.DataFrame:
    base = yearly.loc[yearly["year"].eq(BASE_YEAR)].iloc[0]
    end = yearly.loc[yearly["year"].eq(END_YEAR)].iloc[0]
    base_area = float(base["command_area_ha"])
    end_area = float(end["command_area_ha"])
    base_dams = int(base["n_unique_dams"])
    end_dams = int(end["n_unique_dams"])
    new_area = end_area - base_area
    new_dams = end_dams - base_dams

    rows = [
        {
            "cohort": "Dams active by 2000",
            "n_dams": base_dams,
            "command_area_ha": base_area,
            "share_of_2015_command_area_ha_pct": base_area / end_area * 100 if end_area else np.nan,
            "note": "",
        },
        {
            "cohort": "Additional active dams and net dissolved footprint, 2001-2015",
            "n_dams": new_dams,
            "command_area_ha": new_area,
            "share_of_2015_command_area_ha_pct": new_area / end_area * 100 if end_area else np.nan,
            "note": "Uses yearly dissolved command-area QA, so overlapping envelopes are counted once.",
        },
        {
            "cohort": "All dams active by 2015",
            "n_dams": end_dams,
            "command_area_ha": end_area,
            "share_of_2015_command_area_ha_pct": 100.0,
            "note": "",
        },
    ]
    return pd.DataFrame(rows)


def _figure_growth_decomposition(sensitivity: pd.DataFrame, yearly: pd.DataFrame, figures_dir: Path, manifest_rows: list[dict]) -> None:
    primary = sensitivity[sensitivity["variant"].eq(PRIMARY_TAG)].iloc[0]
    inside_growth = float(primary["inside_growth_ha"])
    outside_growth = float(primary["outside_growth_ha"])
    total_growth = float(primary["total_growth_ha"])
    values = np.array([inside_growth, outside_growth], dtype=float) / 1000
    shares = np.array([primary["inside_growth_share"], primary["outside_growth_share"]], dtype=float) * 100
    colors = ["#277C78", "#C26A2E"]

    base_total = float(yearly.loc[yearly["year"].eq(BASE_YEAR), "total_AEI_ha"].iloc[0])
    contribution_pp = np.array([inside_growth / base_total * 100, outside_growth / base_total * 100])
    thresholds = np.array([0.90, 0.75, 0.50])
    needed = np.maximum(0, (1 - thresholds) * total_growth - inside_growth) / 1000

    fig, axes = plt.subplots(1, 3, figsize=(12.6, 3.9), gridspec_kw={"width_ratios": [1.15, 1.0, 1.05]})

    ax = axes[0]
    ax.barh([0], [values[0]], color=colors[0], height=0.45)
    ax.barh([0], [values[1]], left=[values[0]], color=colors[1], height=0.45)
    ax.set_yticks([])
    ax.set_xlabel("Thousand ha")
    ax.set_title("A. Growth split")
    ax.set_xlim(0, values.sum() * 1.08)
    ax.text(values[0] + values[1] * 0.5, 0, f"Outside\n{shares[1]:.1f}%", ha="center", va="center", color="white", fontsize=11)
    ax.annotate(
        f"Inside {shares[0]:.1f}%\n{values[0]:.1f}k ha",
        xy=(values[0], 0),
        xytext=(values.sum() * 0.12, 0.42),
        arrowprops={"arrowstyle": "-", "color": "#555555", "linewidth": 0.8},
        ha="left",
        va="bottom",
        fontsize=9,
    )
    ax.spines[["top", "right", "left"]].set_visible(False)

    ax = axes[1]
    ax.bar(["Inside", "Outside"], contribution_pp, color=colors, width=0.62)
    ax.set_ylabel("Percentage points of 2000 AEI")
    ax.set_title("B. Common denominator")
    ax.grid(axis="y", color="#D9D9D9", linewidth=0.8)
    for i, value in enumerate(contribution_pp):
        ax.text(i, value + contribution_pp.max() * 0.035, f"{value:.2f}", ha="center", fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)

    ax = axes[2]
    labels = ["Below 90%", "Below 75%", "Below 50%"]
    ax.bar(labels, needed, color="#6B7280", width=0.62)
    ax.set_ylabel("Thousand ha reassigned")
    ax.set_title("C. Missing-dam tipping points")
    ax.grid(axis="y", color="#D9D9D9", linewidth=0.8)
    for i, value in enumerate(needed):
        ax.text(i, value + max(needed) * 0.035, f"{value:.1f}", ha="center", fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)

    fig.suptitle("AEI growth is overwhelmingly outside modeled large-dam command-area envelopes", fontsize=13, y=1.04)
    fig.tight_layout()
    _savefig(figures_dir / "figure_1_growth_decomposition.png", manifest_rows, "figure_1_growth_decomposition")


def _figure_sensitivity(sensitivity: pd.DataFrame, figures_dir: Path, manifest_rows: list[dict]) -> None:
    df = sensitivity.copy()
    df["outside_growth_share_pct"] = pd.to_numeric(df["outside_growth_share"], errors="coerce") * 100
    order = ["area_weighted", "center_cell", "all_touched"]
    df["order"] = df["variant"].map({name: i for i, name in enumerate(order)}).fillna(99)
    df = df.sort_values("order")

    fig = plt.figure(figsize=(8.6, 5.6), constrained_layout=True)
    gs = fig.add_gridspec(2, 3, height_ratios=[1.05, 1.0])
    schematic_axes = [fig.add_subplot(gs[0, i]) for i in range(3)]
    ax = fig.add_subplot(gs[1, :])

    method_titles = {
        "area_weighted": "Area-weighted\nfractional overlap",
        "center_cell": "Cell-center\nmask",
        "all_touched": "All-touched\nmask",
    }
    method_notes = {
        "area_weighted": "Partial cells count by overlap",
        "center_cell": "Cell counts if center is inside",
        "all_touched": "Cell counts if boundary touches it",
    }
    for schematic_ax, variant in zip(schematic_axes, df["variant"]):
        _draw_extraction_schematic(
            schematic_ax,
            method=str(variant),
            title=method_titles.get(str(variant), str(variant)),
            note=method_notes.get(str(variant), ""),
        )

    x = np.arange(len(df))
    colors = np.where(df["is_primary"].astype(str).str.lower().isin({"true", "1"}), "#277C78", "#8E8E8E")
    ax.scatter(x, df["outside_growth_share_pct"], s=82, color=colors, zorder=3)
    ax.plot(x, df["outside_growth_share_pct"], color="#B6B6B6", linewidth=1.2, zorder=2)
    short_labels = {
        "area_weighted": "Area-weighted",
        "center_cell": "Cell-center",
        "all_touched": "All-touched",
    }
    ax.set_xticks(x, [short_labels.get(str(v), str(v)) for v in df["variant"]])
    ymin = max(0, df["outside_growth_share_pct"].min() - 0.35)
    ymax = min(100, df["outside_growth_share_pct"].max() + 0.35)
    ax.set_ylim(ymin, ymax)
    ax.set_ylabel("Outside growth share (%)")
    ax.set_title("Result by method")
    ax.grid(axis="y", color="#D9D9D9", linewidth=0.8)
    for xi, yi in zip(x, df["outside_growth_share_pct"]):
        ax.text(xi, yi + 0.06, f"{yi:.1f}%", ha="center", va="bottom", fontsize=8.5)
    ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Extraction-method sensitivity: how raster cells are assigned to command areas", y=1.03)
    _savefig(figures_dir / "figure_2_extraction_sensitivity.png", manifest_rows, "figure_2_extraction_sensitivity")


def _draw_extraction_schematic(ax, method: str, title: str, note: str) -> None:
    n = 6
    center = np.array([3.08, 3.0])
    radius = 1.85
    sample_offsets = np.linspace(0.08, 0.92, 8)
    sx, sy = np.meshgrid(sample_offsets, sample_offsets)
    sample_points = np.column_stack([sx.ravel(), sy.ravel()])

    for row in range(n):
        for col in range(n):
            pts = sample_points + np.array([col, row])
            dist = np.hypot(pts[:, 0] - center[0], pts[:, 1] - center[1])
            frac = float(np.mean(dist <= radius))
            cell_center = np.array([col + 0.5, row + 0.5])
            center_inside = np.hypot(*(cell_center - center)) <= radius
            if method == "area_weighted":
                fill = "#277C78"
                alpha = 0.12 + 0.75 * frac if frac > 0 else 0.0
            elif method == "center_cell":
                fill = "#277C78" if center_inside else "white"
                alpha = 0.82 if center_inside else 0.0
            else:
                fill = "#277C78" if frac > 0 else "white"
                alpha = 0.82 if frac > 0 else 0.0
            ax.add_patch(Rectangle((col, row), 1, 1, facecolor=fill, alpha=alpha, edgecolor="#C7C7C7", linewidth=0.75))
            if method == "center_cell":
                ax.plot(cell_center[0], cell_center[1], marker=".", markersize=2.2, color="#4B5563")

    ax.add_patch(Circle(center, radius, fill=False, edgecolor="#C26A2E", linewidth=2.0))
    ax.set_xlim(0, n)
    ax.set_ylim(0, n)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title, fontsize=9.5, pad=4)
    ax.text(0.5, -0.12, note, ha="center", va="top", transform=ax.transAxes, fontsize=7.7, color="#4B5563")
    for spine in ax.spines.values():
        spine.set_visible(False)


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


def _figure_top_countries(
    country_table: pd.DataFrame,
    concentration_table: pd.DataFrame,
    figures_dir: Path,
    manifest_rows: list[dict],
) -> None:
    df = country_table.head(12).sort_values("total_growth_ha", ascending=True).copy()
    inside = df["inside_growth_ha"].clip(lower=0) / 1000
    outside = df["outside_growth_ha"].clip(lower=0) / 1000

    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.9), gridspec_kw={"width_ratios": [2.35, 1.0]})
    ax = axes[0]
    ax.barh(df["country_name"], outside, color="#C26A2E", label="Outside")
    ax.barh(df["country_name"], inside, left=outside, color="#277C78", label="Inside")
    ax.set_xlabel("Positive AEI growth, 2000-2015 (thousand ha)")
    ax.set_title("A. Largest country contributors")
    ax.grid(axis="x", color="#D9D9D9", linewidth=0.8)
    ax.legend(frameon=False, loc="lower right")
    ax.spines[["top", "right", "left"]].set_visible(False)

    n_positive = int(_as_float(_metric_value(concentration_table, "Countries with positive total AEI growth", np.nan)))
    n_95 = int(
        _as_float(
            _metric_value(
                concentration_table,
                "Positive-growth countries with at least 95% of growth outside envelopes",
                np.nan,
            )
        )
    )
    n_all = int(
        _as_float(
            _metric_value(concentration_table, "Positive-growth countries with all growth outside envelopes", np.nan)
        )
    )
    inside_exception_share = _as_float(
        _metric_value(concentration_table, "Largest inside-growth country share of regional inside growth (%)", np.nan)
    )
    positive_top = country_table[pd.to_numeric(country_table["total_growth_ha"], errors="coerce").gt(0)].copy()
    senegal = positive_top[positive_top["ISO"].eq("SEN")]
    senegal_share = float(senegal["outside_growth_share_pct"].iloc[0]) if not senegal.empty else np.nan

    ax = axes[1]
    ax.axis("off")
    ax.set_title("B. Pattern check", loc="left")
    stats = [
        (f"{n_95}/{n_positive}", "positive-growth countries\n>=95% outside"),
        (f"{n_all}/{n_positive}", "positive-growth countries\n100% outside"),
        (
            "Senegal",
            (
                f"main inside-growth exception\n{inside_exception_share:.1f}% of inside growth\n{senegal_share:.1f}% outside"
                if pd.notna(senegal_share) and pd.notna(inside_exception_share)
                else "main inside-growth exception"
            ),
        ),
    ]
    y_positions = [0.82, 0.52, 0.22]
    for (value, label), y in zip(stats, y_positions):
        ax.text(0.02, y, value, fontsize=15, fontweight="bold", color="#333333", transform=ax.transAxes)
        ax.text(0.02, y - 0.105, label, fontsize=8.0, color="#4B5563", transform=ax.transAxes, linespacing=1.05)

    fig.suptitle("Country-level growth reinforces the regional outside-envelope result", y=1.02)
    fig.tight_layout()
    _savefig(figures_dir / "figure_4_top_country_growth_contributors.png", manifest_rows, "figure_4_top_country_growth_contributors")


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
    contribution_table = _build_contribution_table(data["sensitivity"], yearly_table)
    concentration_table = _build_concentration_table(data)
    cohort_table = _build_dam_cohort_table(yearly_table)

    _write_table(headline, TABLE_HEADLINE, tables_dir, manifest_rows)
    _write_table(sensitivity_table, TABLE_SENSITIVITY, tables_dir, manifest_rows)
    _write_table(country_table, TABLE_COUNTRIES, tables_dir, manifest_rows)
    _write_table(yearly_table, TABLE_YEARLY, tables_dir, manifest_rows)
    _write_table(contribution_table, TABLE_CONTRIBUTION, tables_dir, manifest_rows)
    _write_table(concentration_table, TABLE_CONCENTRATION, tables_dir, manifest_rows)
    _write_table(cohort_table, TABLE_COHORT, tables_dir, manifest_rows)

    _figure_growth_decomposition(data["sensitivity"], yearly_table, figures_dir, manifest_rows)
    _figure_sensitivity(data["sensitivity"], figures_dir, manifest_rows)
    _figure_timeseries(yearly_table, figures_dir, manifest_rows)
    _figure_top_countries(country_table, concentration_table, figures_dir, manifest_rows)
    _remove_deprecated_assets(figures_dir)

    manifest_path = diagnostics_dir / OUTPUT_MANIFEST
    new_manifest = pd.DataFrame(manifest_rows)
    if manifest_path.exists():
        existing = pd.read_csv(manifest_path)
        rewritten = set(new_manifest["asset_name"]) | set(DEPRECATED_ASSET_NAMES)
        manifest = existing[~existing["asset_name"].isin(rewritten)].copy()
        manifest = pd.concat([manifest, new_manifest], ignore_index=True)
    else:
        manifest = new_manifest
    manifest.to_csv(manifest_path, index=False)
    print(f"Wrote manuscript asset manifest: {manifest_path}")
    print(manifest.to_string(index=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except WorkflowInputError as exc:
        raise SystemExit(f"ERROR: {exc}") from None
