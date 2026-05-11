import os
import zipfile
from contextlib import ExitStack
from pathlib import Path

import numpy as np
import geopandas as gpd
from scipy.spatial import cKDTree
from shapely.ops import unary_union
from tqdm import tqdm
import rasterio
from rasterio.merge import merge
from rasterio.vrt import WarpedVRT
from rasterio.warp import calculate_default_transform, reproject, Resampling


# Import functions from utility.py (use relative import for package)
from .utility import load_config, resolve_path

# Common spatial operations
def calculate_nearest_distances(src_gdf, target_gdf):
    """
    Calculate distances from source points to nearest target points.
    
    Parameters:
    -----------
    src_gdf : GeoDataFrame
        Source geometries
    target_gdf : GeoDataFrame
        Target geometries to find distances to
        
    Returns:
    --------
    numpy.ndarray
        Array of distances from each source point to the nearest target point
    """
    src_centroids = np.array(list(src_gdf.geometry.centroid.apply(lambda geom: (geom.x, geom.y))))
    target_points = np.array(list(target_gdf.geometry.apply(lambda geom: (geom.x, geom.y))))
    
    if len(target_points) == 0:
        return np.array([np.nan] * len(src_centroids))
    
    tree = cKDTree(target_points)
    distances, _ = tree.query(src_centroids, k=1)
    
    return distances

def classify_by_distance_ranges(distances, distance_ranges):
    """
    Classify distances into specified ranges.
    
    Parameters:
    -----------
    distances : numpy.ndarray
        Array of distances to classify
    distance_ranges : list of tuples
        List of (lower_bound, upper_bound) tuples defining the distance ranges
        
    Returns:
    --------
    dict
        Dictionary with range labels as keys and binary arrays as values
    """
    classifications = {}
    for lower_bound, upper_bound in distance_ranges:
        label = f"{int(lower_bound)}-{int(upper_bound)}"
        classifications[label] = np.where(
            (distances >= lower_bound) & (distances < upper_bound), 1, 0)
    return classifications

def optimized_clip(source_gdf, clip_gdf):
    """
    Efficiently clip a GeoDataFrame using centroid-based filtering.
    
    Parameters:
    -----------
    source_gdf : GeoDataFrame
        Source geometries to clip
    clip_gdf : GeoDataFrame
        Geometries to use as the clip boundary
        
    Returns:
    --------
    GeoDataFrame
        Clipped GeoDataFrame
    """
    # Create a unary union of the clip geometries
    clip_union = unary_union(clip_gdf.geometry)

    # Build a centroid GeoDataFrame without modifying source_gdf
    centroids_gdf = gpd.GeoDataFrame(geometry=source_gdf.geometry.centroid, crs=source_gdf.crs)

    # Use spatial join to filter geometries whose centroids intersect the clipping area
    clip_gdf_union = gpd.GeoDataFrame(geometry=[clip_union], crs=clip_gdf.crs)
    joined = gpd.sjoin(centroids_gdf, clip_gdf_union, how="inner", predicate="intersects")

    return source_gdf.loc[joined.index].copy()

# Statistical functions
def bootstrap_targeting_ratio(numerator, denominator, num_bootstrap=10000):
    """
    Calculate confidence intervals for targeting ratio using bootstrap.
    
    Parameters:
    -----------
    numerator : float
        Numerator of the targeting ratio
    denominator : float
        Denominator of the targeting ratio
    num_bootstrap : int, optional
        Number of bootstrap samples, default 10000
        
    Returns:
    --------
    tuple
        (lower_bound, upper_bound) of the 95% confidence interval
    """
    ratios = []
    for _ in range(num_bootstrap):
        boot_numerator = np.random.poisson(numerator)
        boot_denominator = np.random.poisson(denominator)
        if boot_denominator != 0:
            boot_ratio = boot_numerator / boot_denominator
        else:
            boot_ratio = np.nan
        ratios.append(boot_ratio)
    ratios = np.array(ratios)
    return np.nanpercentile(ratios, 2.5), np.nanpercentile(ratios, 97.5)

# Data loading helpers
def load_and_reproject(file_path, target_crs="EPSG:3857"):
    """
    Load a spatial file and reproject to the target CRS.
    
    Parameters:
    -----------
    file_path : str
        Path to the spatial file
    target_crs : str, optional
        Target coordinate reference system, default "EPSG:3857"
        
    Returns:
    --------
    GeoDataFrame
        Loaded and reprojected GeoDataFrame
    """
    try:
        gdf = gpd.read_file(file_path)
        if gdf.crs != target_crs:
            gdf = gdf.to_crs(target_crs)
        return gdf
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None
    
def load_raster_and_reproject(file_path, target_crs="EPSG:4326"):
    """
    Load a raster file and reproject it to the target CRS.
    
    Parameters:
    - file_path : str
    - target_crs : str (e.g., 'EPSG:4326')
    
    Returns:
    - reprojected_data : np.ndarray
    - transform : Affine
    - metadata : dict
    """
    with rasterio.open(file_path) as src:
        if src.crs.to_string() == target_crs:
            data = src.read(1)
            return data, src.transform, src.meta.copy()
        
        transform, width, height = calculate_default_transform(
            src.crs, target_crs, src.width, src.height, *src.bounds)
        
        kwargs = src.meta.copy()
        kwargs.update({
            'crs': target_crs,
            'transform': transform,
            'width': width,
            'height': height
        })

        reprojected_data = np.empty((height, width), dtype=src.meta['dtype'])

        reproject(
            source=rasterio.band(src, 1),
            destination=reprojected_data,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=transform,
            dst_crs=target_crs,
            resampling=Resampling.nearest
        )

        return reprojected_data, transform, kwargs


def _open_hdma_zip_raster(zip_path):
    """Open the single DEM/flow GeoTIFF stored inside a ScienceBase ZIP attachment."""
    zip_path = Path(zip_path)
    with zipfile.ZipFile(zip_path) as zf:
        tif_names = [name for name in zf.namelist() if name.lower().endswith(".tif")]

    if not tif_names:
        raise FileNotFoundError(f"No GeoTIFF found inside {zip_path}")

    tif_name = tif_names[0]
    return rasterio.open(f"zip://{zip_path.resolve().as_posix()}!{tif_name}")


def build_hdma_africa_dem(
    dem_zip_dir,
    output_tif_path,
    aoi_path=None,
    target_crs="EPSG:3857",
    resampling=Resampling.bilinear,
):
    """
    Build a projected Africa DEM crop from the HDMA ScienceBase ZIP tiles.

    The raw HDMA tiles are stored in EPSG:4326. This helper warps the tiles into a
    single projected raster cropped to the supplied AOI, which keeps the output small
    enough for the notebook workflow.
    """
    import time

    dem_zip_dir = Path(dem_zip_dir)
    zip_paths = sorted(dem_zip_dir.glob("*.zip"))
    if not zip_paths:
        raise FileNotFoundError(f"No HDMA DEM ZIP files found in {dem_zip_dir}")
    print(f"Found {len(zip_paths)} HDMA DEM ZIP tiles in {dem_zip_dir}", flush=True)

    bounds = None
    if aoi_path is not None:
        print(f"Loading AOI: {aoi_path}", flush=True)
        aoi = gpd.read_file(aoi_path)
        if aoi.crs is None:
            raise ValueError(f"AOI layer {aoi_path} has no CRS")
        aoi = aoi.to_crs(target_crs)
        bounds = tuple(aoi.total_bounds)
        print(f"AOI bounds ({target_crs}): {bounds}", flush=True)

    output_tif_path = Path(output_tif_path)
    output_tif_path.parent.mkdir(parents=True, exist_ok=True)

    with ExitStack() as stack:
        vrt_sources = []
        for i, zip_path in enumerate(zip_paths, 1):
            print(f"  Opening tile {i}/{len(zip_paths)}: {zip_path.name}", flush=True)
            src = stack.enter_context(_open_hdma_zip_raster(zip_path))
            vrt = stack.enter_context(
                WarpedVRT(
                    src,
                    crs=target_crs,
                    resampling=resampling,
                    dtype="float32",
                    src_nodata=src.nodata,
                    nodata=src.nodata,
                )
            )
            vrt_sources.append(vrt)

        if not vrt_sources:
            raise FileNotFoundError(f"No readable HDMA DEM tiles found in {dem_zip_dir}")

        res = (abs(vrt_sources[0].transform.a), abs(vrt_sources[0].transform.e))
        nodata = vrt_sources[0].nodata
        print(f"Merging {len(vrt_sources)} tiles (this is the slow step — may take 10-30 min)...", flush=True)
        t0 = time.time()
        mosaic, out_transform = merge(
            vrt_sources,
            bounds=bounds,
            res=res,
            nodata=nodata,
            method="first",
        )
        print(f"Merge complete in {(time.time() - t0) / 60:.1f} min. Output shape: {mosaic.shape}", flush=True)

        meta = vrt_sources[0].meta.copy()
        meta.update(
            driver="GTiff",
            height=mosaic.shape[1],
            width=mosaic.shape[2],
            crs=target_crs,
            transform=out_transform,
            nodata=nodata,
            dtype=str(mosaic.dtype),
            compress="DEFLATE",
            tiled=True,
            bigtiff="YES",
        )

        print(f"Writing output: {output_tif_path}", flush=True)
        with rasterio.open(output_tif_path, "w", **meta) as dst:
            dst.write(mosaic)
        print(f"Done. File size: {output_tif_path.stat().st_size / 1e6:.1f} MB", flush=True)

    return str(output_tif_path)


def load_aei_dataset(dataset_type="standard", target_crs="EPSG:3857"):
    """
    Load the appropriate AEI dataset based on the specified type.
    
    Parameters:
    -----------
    dataset_type : str, optional
        Type of dataset to load, either "standard" or "meier", default "standard"
    target_crs : str, optional
        Target coordinate reference system, default "EPSG:3857"
        
    Returns:
    --------
    GeoDataFrame
        Loaded and reprojected AEI GeoDataFrame
    """
    config = load_config()
    
    if dataset_type.lower() == "meier":
        path_key = 'AEI_MEIER_2015_reproj_gpkg_path'
    else:
        path_key = 'AEI_2015_reproj_gpkg_path'
    
    try:
        return load_and_reproject(resolve_path(config[path_key]), target_crs)
    except Exception as e:
        print(f"Error loading {dataset_type} AEI dataset: {e}")
        return None

def process_aei_by_aridity(dataset_type="standard", layers=None):
    """
    Process AEI data by aridity layers.
    
    Parameters:
    -----------
    dataset_type : str, optional
        Type of dataset to process, either "standard" or "meier", default "standard"
    layers : list, optional
        List of aridity layers to process, default ["Semi_Arid", "Arid", "Hyper_Arid", "All"]
        
    Returns:
    --------
    dict
        Dictionary of processed GeoDataFrames by layer
    """
    if layers is None:
        layers = ["Semi_Arid", "Arid", "Hyper_Arid", "All"]
    
    config = load_config()
    results = {}
    
    # Load the main dataset
    aei_gdf = load_aei_dataset(dataset_type)
    if aei_gdf is None:
        print(f"Failed to load {dataset_type} AEI dataset")
        return results
    
    # Load Africa boundaries
    africa_boundaries = load_and_reproject(resolve_path(config['Africa_boundaries_shp_path']), aei_gdf.crs)

    # Process each layer
    for layer in tqdm(layers, desc=f"Processing {dataset_type} AEI by aridity layers"):
        try:
            # Determine the correct paths based on dataset type
            if dataset_type.lower() == "meier":
                output_path = config[f'AEI_MEIER_2015_{layer}_shp_path']
            else:
                output_path = config[f'AEI_2015_{layer}_shp_path']

            # Load the shapefile for the current layer
            gdf_shp = load_and_reproject(resolve_path(config[f'Africa_{layer}_shp_path']), aei_gdf.crs)
            
            # Perform the clip operation
            gdf_cropped = optimized_clip(aei_gdf, gdf_shp)
            
            # Find the centroid of each polygon and perform spatial join
            gdf_cropped['centroid'] = gdf_cropped.geometry.centroid
            centroid_gdf = gpd.GeoDataFrame(geometry=gdf_cropped['centroid'], crs=gdf_cropped.crs)
            joined = gpd.sjoin(centroid_gdf, africa_boundaries[['ISO', 'geometry']], how='left', predicate='intersects')
            
            # Add ISO column to the original GeoDataFrame
            gdf_cropped['ISO'] = joined['ISO']
            
            # Drop unnecessary columns
            gdf_cropped = gdf_cropped.drop(columns=['centroid'])
            
            # Save the result
            gdf_cropped.to_file(resolve_path(output_path), driver='ESRI Shapefile')
            results[layer] = gdf_cropped
            
            print(f"{layer} layer processed and saved to {output_path}")
        except Exception as e:
            print(f"Error processing {layer} layer: {e}")
    
    return results

def generate_distance_ranges(min_dist=0, max_dist=100000, num_intervals=10):
    """
    Generate distance range intervals.
    
    Parameters:
    -----------
    min_dist : float, optional
        Minimum distance, default 0
    max_dist : float, optional
        Maximum distance, default 100000
    num_intervals : int, optional
        Number of intervals, default 10
        
    Returns:
    --------
    list
        List of (lower_bound, upper_bound) tuples
    """
    interval_edges = np.linspace(min_dist, max_dist, num=num_intervals+1)
    return [(interval_edges[i], interval_edges[i+1]) for i in range(len(interval_edges)-1)]
