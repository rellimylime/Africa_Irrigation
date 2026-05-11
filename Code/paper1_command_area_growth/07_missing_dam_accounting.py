"""Account for incomplete dam coverage using growth-rate and bounds logic.

This step asks whether the conclusion depends on observing every dam. Instead of
requiring a complete dam inventory, it treats the modeled command-area layer as a
sample of dam-associated irrigation. If the probability of observing a relevant
large dam is roughly stable over time, the sample growth rate is informative even
when the absolute level is incomplete. If the sample grows faster than total AEI,
this rate test does not support a declining-share claim; the tipping-point bounds
remain useful for transparent interpretation.

The script reports:
- total AEI growth rate;
- dam-associated AEI growth rate inside sampled command-area envelopes;
- the missing-dam growth rate required to make all dam-associated irrigation grow
  as fast as total AEI under several assumptions about the missing baseline stock;
- tipping-point amounts needed to move the outside-growth share below common
  thresholds.
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

from paper1_common import WorkflowInputError, config_path, ensure_paper_dirs, final_tables_dir, paper_dir


BASE_YEAR = 2000
END_YEAR = 2015
PRIMARY_TAG = "area_weighted"

RATE_TABLE = "paper1_missing_dam_growth_rate_accounting.csv"
TIPPING_TABLE = "paper1_missing_dam_tipping_points.csv"
COUNTRY_TABLE = "paper1_country_growth_rate_comparison.csv"
TABLE_OUTPUT = "table_6_missing_dam_accounting.csv"
FIG_OUTPUT = "figure_8_missing_dam_tipping_points.png"
DEPRECATED_FIGURES = ("figure_8_missing_dam_growth_rate_bounds.png",)
DEPRECATED_ASSET_NAMES = ("figure_8_missing_dam_growth_rate_bounds",)


def _tagged_csv_path(path: Path, output_tag: str | None) -> Path:
    if output_tag is None:
        return path
    tag = output_tag.strip().replace("-", "_")
    if not tag or not tag.replace("_", "").isalnum():
        raise WorkflowInputError(f"Invalid output tag: {output_tag!r}")
    return path.with_name(f"{path.stem}_{tag}{path.suffix}")


def _read_one_row(path: Path) -> pd.Series:
    if not path.exists():
        raise WorkflowInputError(f"Missing required table: {path}")
    df = pd.read_csv(path)
    if len(df) != 1:
        raise WorkflowInputError(f"Expected one row in {path}, found {len(df)}")
    return df.iloc[0]


def _annualized_growth_rate(base: float, end: float, years: int) -> float:
    if base <= 0 or end <= 0 or years <= 0:
        return np.nan
    return (end / base) ** (1 / years) - 1


def _required_missing_growth_rate(
    observed_base: float,
    observed_end: float,
    total_growth_rate: float,
    missing_base_multiplier: float,
    years: int,
) -> tuple[float, float, float, float]:
    missing_base = observed_base * missing_base_multiplier
    missing_end_needed = (observed_base + missing_base) * ((1 + total_growth_rate) ** years) - observed_end
    missing_growth = missing_end_needed - missing_base
    missing_rate = _annualized_growth_rate(missing_base, missing_end_needed, years) if missing_base > 0 else np.nan
    return missing_base, missing_end_needed, missing_growth, missing_rate


def _write_manifest_rows(rows: list[dict]) -> None:
    manifest_path = paper_dir("Paper1_diagnostics_dir") / "paper1_manuscript_asset_manifest.csv"
    if manifest_path.exists():
        manifest = pd.read_csv(manifest_path)
        manifest = manifest[~manifest["asset_name"].isin({row["asset_name"] for row in rows})]
        manifest = pd.concat([manifest, pd.DataFrame(rows)], ignore_index=True)
    else:
        manifest = pd.DataFrame(rows)
    manifest.to_csv(manifest_path, index=False)


def _build_tables() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    summary_path = _tagged_csv_path(config_path("Paper1_growth_summary_csv_path"), PRIMARY_TAG)
    country_path = _tagged_csv_path(config_path("Paper1_growth_decomposition_csv_path"), PRIMARY_TAG)
    summary = _read_one_row(summary_path)
    if not country_path.exists():
        raise WorkflowInputError(f"Missing country growth table: {country_path}")
    country = pd.read_csv(country_path)

    years = int(summary["end_year"] - summary["base_year"])
    total_base = float(summary["total_AEI_ha_base"])
    total_end = float(summary["total_AEI_ha_end"])
    inside_base = float(summary["inside_AEI_ha_base"])
    inside_end = float(summary["inside_AEI_ha_end"])
    outside_growth = float(summary["outside_growth_ha"])
    total_growth = float(summary["total_growth_ha"])

    total_rate = _annualized_growth_rate(total_base, total_end, years)
    inside_rate = _annualized_growth_rate(inside_base, inside_end, years)
    absolute_rate_gap = total_rate - inside_rate
    relative_rate_ratio = inside_rate / total_rate if total_rate else np.nan

    rate_rows = [
        {
            "quantity": "total_AEI",
            "base_year": BASE_YEAR,
            "end_year": END_YEAR,
            "base_ha": total_base,
            "end_ha": total_end,
            "growth_ha": total_growth,
            "annualized_growth_rate": total_rate,
            "annualized_growth_rate_pct": total_rate * 100,
        },
        {
            "quantity": "sampled_dam_associated_AEI_inside_command_areas",
            "base_year": BASE_YEAR,
            "end_year": END_YEAR,
            "base_ha": inside_base,
            "end_ha": inside_end,
            "growth_ha": inside_end - inside_base,
            "annualized_growth_rate": inside_rate,
            "annualized_growth_rate_pct": inside_rate * 100,
        },
        {
            "quantity": "growth_rate_gap_total_minus_sampled_dam_associated",
            "base_year": BASE_YEAR,
            "end_year": END_YEAR,
            "base_ha": np.nan,
            "end_ha": np.nan,
            "growth_ha": np.nan,
            "annualized_growth_rate": absolute_rate_gap,
            "annualized_growth_rate_pct": absolute_rate_gap * 100,
        },
    ]
    rates = pd.DataFrame(rate_rows)

    multipliers = [0.25, 0.5, 1, 2, 5, 10]
    missing_rows = []
    for multiplier in multipliers:
        missing_base, missing_end_needed, missing_growth, missing_rate = _required_missing_growth_rate(
            observed_base=inside_base,
            observed_end=inside_end,
            total_growth_rate=total_rate,
            missing_base_multiplier=multiplier,
            years=years,
        )
        missing_rows.append(
            {
                "missing_baseline_stock_assumption": f"{multiplier:g}x observed sampled dam-associated AEI in {BASE_YEAR}",
                "missing_base_multiplier": multiplier,
                "observed_inside_base_ha": inside_base,
                "observed_inside_end_ha": inside_end,
                "missing_base_ha_assumed": missing_base,
                "missing_end_ha_required_for_total_rate": missing_end_needed,
                "missing_growth_ha_required": missing_growth,
                "missing_annualized_growth_rate_required": missing_rate,
                "missing_annualized_growth_rate_required_pct": missing_rate * 100,
                "total_AEI_annualized_growth_rate_pct": total_rate * 100,
                "observed_inside_annualized_growth_rate_pct": inside_rate * 100,
                "required_missing_rate_minus_total_rate_pct_points": (missing_rate - total_rate) * 100,
                "interpretation": (
                    "Assumed growth rate for the missing baseline stock that would make observed plus missing "
                    "dam-associated irrigation grow at the same annualized rate as total AEI."
                ),
            }
        )
    missing = pd.DataFrame(missing_rows)

    thresholds = [0.90, 0.75, 0.50]
    tipping_rows = []
    for threshold in thresholds:
        inside_needed = (1 - threshold) * total_growth
        additional_inside_needed = max(0.0, inside_needed - float(summary["inside_growth_ha"]))
        tipping_rows.append(
            {
                "target_outside_growth_share": threshold,
                "target_outside_growth_share_pct": threshold * 100,
                "observed_outside_growth_share_pct": float(summary["outside_growth_share"]) * 100,
                "total_growth_ha": total_growth,
                "observed_inside_growth_ha": float(summary["inside_growth_ha"]),
                "observed_outside_growth_ha": outside_growth,
                "additional_missing_dam_growth_needed_inside_ha": additional_inside_needed,
                "share_of_observed_outside_growth_that_would_need_reassignment_pct": (
                    additional_inside_needed / outside_growth * 100 if outside_growth else np.nan
                ),
            }
        )
    tipping = pd.DataFrame(tipping_rows)

    country = country.copy()
    country["total_annualized_growth_rate_pct"] = country.apply(
        lambda r: _annualized_growth_rate(float(r["total_AEI_ha_base"]), float(r["total_AEI_ha_end"]), years) * 100,
        axis=1,
    )
    country["inside_annualized_growth_rate_pct"] = country.apply(
        lambda r: _annualized_growth_rate(float(r["inside_AEI_ha_base"]), float(r["inside_AEI_ha_end"]), years) * 100,
        axis=1,
    )
    country["growth_rate_gap_pct_points"] = country["total_annualized_growth_rate_pct"] - country["inside_annualized_growth_rate_pct"]
    country_out = country[
        [
            "ISO",
            "country_name",
            "inside_AEI_ha_base",
            "inside_AEI_ha_end",
            "total_AEI_ha_base",
            "total_AEI_ha_end",
            "inside_growth_ha",
            "outside_growth_ha",
            "total_growth_ha",
            "outside_growth_share",
            "inside_annualized_growth_rate_pct",
            "total_annualized_growth_rate_pct",
            "growth_rate_gap_pct_points",
        ]
    ].copy()

    manuscript = pd.DataFrame(
        [
            {
                "metric": "Total AEI annualized growth rate, 2000-2015 (%)",
                "value": total_rate * 100,
            },
            {
                "metric": "Sampled dam-associated AEI annualized growth rate, 2000-2015 (%)",
                "value": inside_rate * 100,
            },
            {
                "metric": "Growth-rate gap, total minus sampled dam-associated (percentage points)",
                "value": absolute_rate_gap * 100,
            },
            {
                "metric": "Sampled dam-associated growth rate as fraction of total AEI growth rate",
                "value": relative_rate_ratio,
            },
            {
                "metric": "Additional missing-dam growth needed to reduce outside-growth share below 90% (ha)",
                "value": tipping.loc[tipping["target_outside_growth_share"].eq(0.90), "additional_missing_dam_growth_needed_inside_ha"].iloc[0],
            },
            {
                "metric": "Additional missing-dam growth needed to reduce outside-growth share below 75% (ha)",
                "value": tipping.loc[tipping["target_outside_growth_share"].eq(0.75), "additional_missing_dam_growth_needed_inside_ha"].iloc[0],
            },
            {
                "metric": "Additional missing-dam growth needed to reduce outside-growth share below 50% (ha)",
                "value": tipping.loc[tipping["target_outside_growth_share"].eq(0.50), "additional_missing_dam_growth_needed_inside_ha"].iloc[0],
            },
        ]
    )
    return rates, missing, tipping, country_out, manuscript


def _plot_tipping_points(tipping: pd.DataFrame) -> Path:
    figures_dir = paper_dir("Paper1_figures_dir")
    df = tipping.copy()
    df["additional_missing_dam_growth_needed_inside_kha"] = df["additional_missing_dam_growth_needed_inside_ha"] / 1000
    df["target_label"] = df["target_outside_growth_share_pct"].map(lambda value: f"Below {value:.0f}%")

    fig, ax = plt.subplots(figsize=(7.0, 4.4))
    bars = ax.bar(
        df["target_label"],
        df["additional_missing_dam_growth_needed_inside_kha"],
        color=["#A8A29E", "#78716C", "#44403C"],
        width=0.62,
    )
    ymax = df["additional_missing_dam_growth_needed_inside_kha"].max() * 1.28
    ax.set_ylim(0, ymax)
    ax.set_ylabel("Additional inside-envelope growth needed (thousand ha)", fontsize=10)
    ax.set_xlabel("Target outside-growth share", fontsize=10)
    ax.set_title("Missing-dam tipping points", fontsize=12, pad=12)
    ax.grid(axis="y", color="#D9D9D9", linewidth=0.8)
    ax.set_axisbelow(True)
    for bar, share in zip(bars, df["share_of_observed_outside_growth_that_would_need_reassignment_pct"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + df["additional_missing_dam_growth_needed_inside_kha"].max() * 0.04,
            f"{bar.get_height():.1f}k ha\n({share:.1f}% of outside)",
            ha="center",
            va="bottom",
            fontsize=8.5,
        )
    ax.spines[["top", "right"]].set_visible(False)
    out = figures_dir / FIG_OUTPUT
    fig.tight_layout()
    plt.savefig(out, dpi=300, bbox_inches="tight")
    plt.close()
    return out


def _update_manifest(rows: list[dict]) -> None:
    manifest_path = paper_dir("Paper1_diagnostics_dir") / "paper1_manuscript_asset_manifest.csv"
    stale_names = {row["asset_name"] for row in rows} | set(DEPRECATED_ASSET_NAMES)
    if manifest_path.exists():
        manifest = pd.read_csv(manifest_path)
        manifest = manifest[~manifest["asset_name"].isin(stale_names)]
        manifest = pd.concat([manifest, pd.DataFrame(rows)], ignore_index=True)
    else:
        manifest = pd.DataFrame(rows)
    manifest.to_csv(manifest_path, index=False)


def _remove_deprecated_figures() -> None:
    figures_dir = paper_dir("Paper1_figures_dir")
    for name in DEPRECATED_FIGURES:
        path = figures_dir / name
        if path.exists():
            path.unlink()


def main() -> int:
    ensure_paper_dirs()
    rates, missing, tipping, country, manuscript = _build_tables()

    final_dir = final_tables_dir()
    tables_dir = paper_dir("Paper1_tables_dir")
    rates_path = final_dir / RATE_TABLE
    missing_path = final_dir / "paper1_missing_dam_required_growth_rates.csv"
    tipping_path = final_dir / TIPPING_TABLE
    country_path = final_dir / COUNTRY_TABLE
    manuscript_path = tables_dir / TABLE_OUTPUT

    rates.to_csv(rates_path, index=False)
    missing.to_csv(missing_path, index=False)
    tipping.to_csv(tipping_path, index=False)
    country.to_csv(country_path, index=False)
    manuscript.to_csv(manuscript_path, index=False)
    _remove_deprecated_figures()
    fig_path = _plot_tipping_points(tipping)

    _update_manifest(
        [
            {"asset_type": "final_table_csv", "asset_name": "paper1_missing_dam_growth_rate_accounting", "path": str(rates_path)},
            {"asset_type": "final_table_csv", "asset_name": "paper1_missing_dam_required_growth_rates", "path": str(missing_path)},
            {"asset_type": "final_table_csv", "asset_name": "paper1_missing_dam_tipping_points", "path": str(tipping_path)},
            {"asset_type": "final_table_csv", "asset_name": "paper1_country_growth_rate_comparison", "path": str(country_path)},
            {"asset_type": "table_csv", "asset_name": "table_6_missing_dam_accounting", "path": str(manuscript_path)},
            {"asset_type": "figure_png", "asset_name": "figure_8_missing_dam_tipping_points", "path": str(fig_path)},
        ]
    )

    print(f"Wrote growth-rate accounting: {rates_path}")
    print(f"Wrote missing-dam required growth rates: {missing_path}")
    print(f"Wrote tipping-point table: {tipping_path}")
    print(f"Wrote country growth-rate comparison: {country_path}")
    print(f"Wrote manuscript table: {manuscript_path}")
    print(f"Wrote figure: {fig_path}")
    print(manuscript.round(3).to_string(index=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except WorkflowInputError as exc:
        raise SystemExit(f"ERROR: {exc}") from None
