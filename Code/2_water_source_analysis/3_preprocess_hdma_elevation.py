"""Build the projected Africa DEM crop used by the elevation-aware dam analysis."""

from __future__ import annotations

import argparse
import os
import sys


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from Code.utils.spatial_utility import build_hdma_africa_dem
from Code.utils.utility import load_config, resolve_path


def main() -> None:
    config = load_config()

    parser = argparse.ArgumentParser(description="Build the HDMA-derived Africa DEM crop.")
    parser.add_argument(
        "--dem-zip-dir",
        default=resolve_path(config.get("Africa_HDMA_DEM_zip_dir_path", config["Africa_Elevation_rast_path"])),
        help="Directory containing the HDMA Africa DEM ZIP tiles.",
    )
    parser.add_argument(
        "--aoi-path",
        default=resolve_path(config["SSA_All_by_Country_shp_path"]),
        help="AOI shapefile used to crop the DEM output.",
    )
    parser.add_argument(
        "--output",
        default=resolve_path(config["Africa_Elevation_Reprojected_tif_path"]),
        help="Projected DEM output path.",
    )
    parser.add_argument(
        "--target-crs",
        default="EPSG:3857",
        help="Target CRS for the projected output.",
    )

    args = parser.parse_args()

    out_path = build_hdma_africa_dem(
        dem_zip_dir=args.dem_zip_dir,
        output_tif_path=args.output,
        aoi_path=args.aoi_path,
        target_crs=args.target_crs,
    )
    print(f"Built projected DEM: {out_path}")


if __name__ == "__main__":
    main()
