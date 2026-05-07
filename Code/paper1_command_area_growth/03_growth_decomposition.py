"""Decompose AEI growth into inside-command-area and outside-command-area components."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from paper1_common import WorkflowInputError, config_path, ensure_paper_dirs


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


def _growth_share(part: float, total: float) -> float:
    if total == 0 or not np.isfinite(total):
        return np.nan
    return part / total


def _first_nonempty(values: pd.Series):
    for value in values:
        if pd.notna(value) and str(value).strip() and str(value).strip().lower() not in {"nan", "none"}:
            return value
    return pd.NA


def _aggregate_panel_by_country_year(panel: pd.DataFrame) -> pd.DataFrame:
    """Guarantee one row per ISO-year before comparing base and end years."""

    value_cols = ["inside_AEI_ha", "outside_AEI_ha", "total_AEI_ha"]
    panel = panel.copy()
    panel["ISO"] = panel["ISO"].astype(str).str.strip().replace({"nan": pd.NA, "None": pd.NA})
    panel = panel.dropna(subset=["ISO", "year"]).copy()
    panel["year"] = pd.to_numeric(panel["year"], errors="coerce")
    panel = panel.dropna(subset=["year"]).copy()
    panel["year"] = panel["year"].astype(int)
    for col in value_cols:
        panel[col] = pd.to_numeric(panel[col], errors="coerce").fillna(0.0)

    values = panel.groupby(["year", "ISO"], as_index=False)[value_cols].sum()
    names = panel.groupby(["year", "ISO"])["country_name"].agg(_first_nonempty).reset_index()
    out = values.merge(names, on=["year", "ISO"], how="left")
    out["inside_share"] = out.apply(lambda row: _growth_share(row["inside_AEI_ha"], row["total_AEI_ha"]), axis=1)
    out["outside_share"] = out.apply(lambda row: _growth_share(row["outside_AEI_ha"], row["total_AEI_ha"]), axis=1)
    return out


def decompose_growth(panel: pd.DataFrame, base_year: int | None, end_year: int | None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return country-level and aggregate growth decomposition tables."""

    required = {"year", "ISO", "country_name", "inside_AEI_ha", "outside_AEI_ha", "total_AEI_ha"}
    missing = required - set(panel.columns)
    if missing:
        raise WorkflowInputError(f"Inside/outside panel is missing required columns: {', '.join(sorted(missing))}")

    panel = _aggregate_panel_by_country_year(panel)
    years = sorted(int(y) for y in panel["year"].dropna().unique())
    if len(years) < 2:
        raise WorkflowInputError("Growth decomposition needs at least two years in the panel.")
    base_year = base_year if base_year is not None else years[0]
    end_year = end_year if end_year is not None else years[-1]

    if base_year not in years or end_year not in years:
        raise WorkflowInputError(f"Requested years {base_year}->{end_year} are not both present. Available years: {years}")
    if end_year <= base_year:
        raise WorkflowInputError("End year must be later than base year.")

    base = panel[panel["year"].eq(base_year)].copy()
    end = panel[panel["year"].eq(end_year)].copy()

    merged = base.merge(
        end,
        on=["ISO"],
        suffixes=("_base", "_end"),
        how="outer",
    )
    merged["country_name"] = merged["country_name_end"].combine_first(merged["country_name_base"])
    for col in (
        "inside_AEI_ha_base",
        "outside_AEI_ha_base",
        "total_AEI_ha_base",
        "inside_AEI_ha_end",
        "outside_AEI_ha_end",
        "total_AEI_ha_end",
    ):
        merged[col] = pd.to_numeric(merged[col], errors="coerce").fillna(0.0)

    merged["base_year"] = base_year
    merged["end_year"] = end_year
    merged["inside_growth_ha"] = merged["inside_AEI_ha_end"] - merged["inside_AEI_ha_base"]
    merged["outside_growth_ha"] = merged["outside_AEI_ha_end"] - merged["outside_AEI_ha_base"]
    merged["total_growth_ha"] = merged["total_AEI_ha_end"] - merged["total_AEI_ha_base"]
    merged["inside_growth_share"] = merged.apply(
        lambda row: _growth_share(row["inside_growth_ha"], row["total_growth_ha"]), axis=1
    )
    merged["outside_growth_share"] = merged.apply(
        lambda row: _growth_share(row["outside_growth_ha"], row["total_growth_ha"]), axis=1
    )
    merged["outside_share_base"] = merged.apply(
        lambda row: _growth_share(row["outside_AEI_ha_base"], row["total_AEI_ha_base"]), axis=1
    )
    merged["outside_share_end"] = merged.apply(
        lambda row: _growth_share(row["outside_AEI_ha_end"], row["total_AEI_ha_end"]), axis=1
    )
    merged["growth_direction"] = np.select(
        [merged["total_growth_ha"] > 0, merged["total_growth_ha"] < 0],
        ["positive", "negative"],
        default="zero",
    )

    country_cols = [
        "base_year",
        "end_year",
        "ISO",
        "country_name",
        "inside_AEI_ha_base",
        "outside_AEI_ha_base",
        "total_AEI_ha_base",
        "inside_AEI_ha_end",
        "outside_AEI_ha_end",
        "total_AEI_ha_end",
        "inside_growth_ha",
        "outside_growth_ha",
        "total_growth_ha",
        "inside_growth_share",
        "outside_growth_share",
        "outside_share_base",
        "outside_share_end",
        "growth_direction",
    ]
    country = merged[country_cols].sort_values(["growth_direction", "total_growth_ha"], ascending=[True, False])

    summary_source = country
    summary = pd.DataFrame(
        [
            {
                "base_year": base_year,
                "end_year": end_year,
                "scope": "all_panel_countries",
                "n_countries": int(summary_source["ISO"].nunique()),
                "inside_AEI_ha_base": float(summary_source["inside_AEI_ha_base"].sum()),
                "outside_AEI_ha_base": float(summary_source["outside_AEI_ha_base"].sum()),
                "total_AEI_ha_base": float(summary_source["total_AEI_ha_base"].sum()),
                "inside_AEI_ha_end": float(summary_source["inside_AEI_ha_end"].sum()),
                "outside_AEI_ha_end": float(summary_source["outside_AEI_ha_end"].sum()),
                "total_AEI_ha_end": float(summary_source["total_AEI_ha_end"].sum()),
            }
        ]
    )
    summary["inside_growth_ha"] = summary["inside_AEI_ha_end"] - summary["inside_AEI_ha_base"]
    summary["outside_growth_ha"] = summary["outside_AEI_ha_end"] - summary["outside_AEI_ha_base"]
    summary["total_growth_ha"] = summary["total_AEI_ha_end"] - summary["total_AEI_ha_base"]
    summary["inside_growth_share"] = summary.apply(
        lambda row: _growth_share(row["inside_growth_ha"], row["total_growth_ha"]), axis=1
    )
    summary["outside_growth_share"] = summary.apply(
        lambda row: _growth_share(row["outside_growth_ha"], row["total_growth_ha"]), axis=1
    )
    summary["outside_share_base"] = summary.apply(
        lambda row: _growth_share(row["outside_AEI_ha_base"], row["total_AEI_ha_base"]), axis=1
    )
    summary["outside_share_end"] = summary.apply(
        lambda row: _growth_share(row["outside_AEI_ha_end"], row["total_AEI_ha_end"]), axis=1
    )

    return country, summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-year", type=int, default=None, help="Baseline year. Default: earliest panel year.")
    parser.add_argument("--end-year", type=int, default=None, help="End year. Default: latest panel year.")
    parser.add_argument("--panel-path", default=None, help="Inside/outside panel CSV to decompose. Default: configured canonical panel.")
    parser.add_argument(
        "--output-tag",
        default=None,
        help="Read/write variant CSVs with this tag when --panel-path is omitted; always tags growth outputs.",
    )
    args = parser.parse_args(argv)

    ensure_paper_dirs()
    panel_path = (
        Path(args.panel_path)
        if args.panel_path is not None
        else _tagged_csv_path(config_path("Paper1_inside_outside_panel_csv_path"), args.output_tag)
    )
    if not panel_path.exists():
        raise WorkflowInputError(f"Missing inside/outside panel: {panel_path}")

    panel = pd.read_csv(panel_path)
    country, summary = decompose_growth(panel, args.base_year, args.end_year)

    country_path = _tagged_csv_path(config_path("Paper1_growth_decomposition_csv_path"), args.output_tag)
    summary_path = _tagged_csv_path(config_path("Paper1_growth_summary_csv_path"), args.output_tag)
    country_path.parent.mkdir(parents=True, exist_ok=True)
    country.to_csv(country_path, index=False)
    summary.to_csv(summary_path, index=False)

    print(f"Wrote country growth decomposition: {country_path}")
    print(f"Wrote growth summary: {summary_path}")
    print(summary.round(3).to_string(index=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except WorkflowInputError as exc:
        raise SystemExit(f"ERROR: {exc}") from None
