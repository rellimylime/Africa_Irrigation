"""Shared helpers for the command-area growth paper workflow.

The scripts in this folder are intentionally conservative: they write stable CSVs
and GeoPackages, keep the research estimand explicit, and stop early with clear
missing-input messages instead of silently falling back to notebook state.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from Code.utils.utility import load_config, resolve_path


AEI_YEARS: tuple[int, ...] = (1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015)
CPIS_YEARS: tuple[int, ...] = (2000, 2021)

# Africa Albers Equal Area, used only for vector areas. Raster extraction keeps
# rasters in their native grid and reprojects masks to the raster CRS.
AFRICA_EQUAL_AREA_CRS = (
    "+proj=aea +lat_1=-18 +lat_2=21 +lat_0=0 +lon_0=25 "
    "+x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
)

COMMAND_AREA_LAYER = "command_area"
YEARLY_COMMAND_AREA_TEMPLATE = "command_areas_{year}.gpkg"
YEARLY_COMMAND_AREA_INVENTORY = "yearly_command_area_inventory.csv"
EXTRACTION_DIAGNOSTICS = "inside_outside_extraction_diagnostics.csv"


class WorkflowInputError(RuntimeError):
    """Raised when a required workflow input is unavailable or ambiguous."""


@dataclass(frozen=True)
class VectorSource:
    """Resolved vector dataset information."""

    key: str
    path: Path
    note: str = ""


def config() -> dict:
    """Return the repository configuration."""

    return load_config()


def config_path(key: str) -> Path:
    """Resolve a config key to an absolute Path."""

    cfg = config()
    if key not in cfg or cfg[key] in (None, ""):
        raise WorkflowInputError(f"Missing config key: {key}")
    return Path(resolve_path(cfg[key]))


def paper_dir(key: str) -> Path:
    """Resolve and create a paper output directory."""

    path = config_path(key)
    path.mkdir(parents=True, exist_ok=True)
    return path


def final_tables_dir() -> Path:
    return paper_dir("Paper1_final_tables_dir")


def yearly_command_area_dir() -> Path:
    return paper_dir("Paper1_yearly_command_areas_dir")


def extracted_irrigation_dir() -> Path:
    return paper_dir("Paper1_extracted_irrigation_dir")


def ensure_paper_dirs() -> None:
    """Create the canonical paper output folders."""

    for key in (
        "Paper1_processed_dir",
        "Paper1_yearly_command_areas_dir",
        "Paper1_extracted_irrigation_dir",
        "Paper1_final_tables_dir",
        "Paper1_output_dir",
        "Paper1_figures_dir",
        "Paper1_tables_dir",
        "Paper1_diagnostics_dir",
    ):
        if key in config():
            Path(resolve_path(config()[key])).mkdir(parents=True, exist_ok=True)


def existing_path_for_config_key(key: str) -> Path | None:
    """Resolve a config key and return the path only if it exists."""

    try:
        path = config_path(key)
    except WorkflowInputError:
        return None
    return path if path.exists() else None


def find_vector_path(key: str, preferred_stems: Sequence[str] | None = None) -> VectorSource:
    """Resolve a vector file from a config key that may point to a file or folder.

    Several legacy config entries point to shapefile directories rather than a
    specific .shp file. This helper makes those entries usable in scripts while
    still failing if the folder is empty or ambiguous.
    """

    preferred_stems = tuple(preferred_stems or ())
    path = config_path(key)
    if path.is_file():
        return VectorSource(key=key, path=path, note="configured file")
    if not path.exists():
        raise WorkflowInputError(f"Missing vector input for {key}: {path}")
    if not path.is_dir():
        raise WorkflowInputError(f"Configured vector input is not a file or directory: {path}")

    candidates = sorted(
        [
            p
            for p in path.iterdir()
            if p.suffix.lower() in {".shp", ".gpkg", ".geojson", ".json"}
        ]
    )
    if not candidates:
        raise WorkflowInputError(f"No vector files found inside {path} for config key {key}")

    for stem in preferred_stems:
        matches = [p for p in candidates if p.stem.lower() == stem.lower()]
        if len(matches) == 1:
            return VectorSource(key=key, path=matches[0], note=f"matched preferred stem {stem}")

    if len(candidates) == 1:
        return VectorSource(key=key, path=candidates[0], note="only vector file in configured folder")

    names = ", ".join(p.name for p in candidates[:10])
    raise WorkflowInputError(
        f"Multiple vector files found inside {path} for {key}; pass a more specific path/key. "
        f"Candidates include: {names}"
    )


def first_existing_vector(keys: Sequence[str], preferred_stems: Sequence[str] | None = None) -> VectorSource:
    """Return the first configured vector source that resolves successfully."""

    errors: list[str] = []
    for key in keys:
        try:
            return find_vector_path(key, preferred_stems=preferred_stems)
        except WorkflowInputError as exc:
            errors.append(str(exc))
    raise WorkflowInputError("No usable vector source found:\n- " + "\n- ".join(errors))


def find_column(columns: Iterable[str], candidates: Sequence[str], required_label: str) -> str:
    """Find a column by exact or case-insensitive candidate names."""

    cols = list(columns)
    for candidate in candidates:
        if candidate in cols:
            return candidate
    lowered = {c.lower(): c for c in cols}
    for candidate in candidates:
        match = lowered.get(candidate.lower())
        if match is not None:
            return match
    raise WorkflowInputError(
        f"Could not find {required_label}. Tried: {', '.join(candidates)}. "
        f"Available columns: {', '.join(cols)}"
    )


def yearly_command_area_path(year: int, command_area_dir: Path | None = None) -> Path:
    """Return the canonical command-area GeoPackage path for a year."""

    root = command_area_dir or yearly_command_area_dir()
    return root / YEARLY_COMMAND_AREA_TEMPLATE.format(year=year)


def parse_years(raw_years: Sequence[str] | None, default: Sequence[int] = AEI_YEARS) -> list[int]:
    """Parse CLI years into sorted unique integers."""

    if not raw_years:
        return list(default)
    years = sorted({int(y) for y in raw_years})
    return years


def existing_aei_raster_path(year: int) -> Path | None:
    """Return the configured raw AEI raster for a year if present."""

    key = f"Africa_AEI_{year}_asc_path"
    path = existing_path_for_config_key(key)
    return path if path and path.is_file() else None


def available_aei_years(years: Sequence[int] = AEI_YEARS) -> list[int]:
    """List years with local raw AEI rasters."""

    return [year for year in years if existing_aei_raster_path(year) is not None]

