import os
import inspect
import yaml
import numpy as np
import pandas as pd
import geopandas as gpd
from scipy.spatial import cKDTree
from shapely.ops import unary_union
from tqdm import tqdm

# Access to project base_path
def load_config():
    with open('../../config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    return config

def resolve_path(relative_path):
    """Resolve a relative path using the base_path from config."""
    config = load_config()
    return os.path.join(config['base_path'], relative_path)

def resolve_direct_path(base_path, relative_path):
    """Resolve a relative path using a directly provided base_path.
    
    This function allows files to define their own base_path and paths
    without relying on the config.yaml file.
    
    Parameters:
    -----------
    base_path : str
        The base path to use for resolution
    relative_path : str
        The relative path to resolve
        
    Returns:
    --------
    str
        The resolved absolute path
    """
    return os.path.join(base_path, relative_path)

# SSA countries with ISOs dictionary
africa_iso_countries_filtered = {
    "AGO": ["Angola"],
    "BEN": ["Benin"],
    "BWA": ["Botswana"],
    "BFA": ["Burkina Faso"],
    "BDI": ["Burundi"],
    "CMR": ["Cameroon"],
    "CAF": ["Central African Republic"],
    "TCD": ["Chad"],
    "CIV": ["Côte d'Ivoire", "CÃ´te d'Ivoire"],
    "COM": ["Comoros"],
    "COG": ["Republic of Congo", "Congo"],
    "COD": ["Democratic Republic of the Congo"],
    "DJI": ["Djibouti"],
    "GNQ": ["Equatorial Guinea"],
    "ERI": ["Eritrea"],
    "SWZ": ["Eswatini", "Swaziland"],
    "ETH": ["Ethiopia"],
    "GAB": ["Gabon"],
    "GMB": ["Gambia"],
    "GHA": ["Ghana"],
    "GIN": ["Guinea"],
    "GNB": ["Guinea-Bissau"],
    "KEN": ["Kenya"],
    "LSO": ["Lesotho"],
    "LBR": ["Liberia"],
    "MDG": ["Madagascar"],
    "MWI": ["Malawi"],
    "MLI": ["Mali"],
    "MRT": ["Mauritania"],
    "MOZ": ["Mozambique"],
    "NAM": ["Namibia"],
    "NER": ["Niger"],
    "NGA": ["Nigeria"],
    "RWA": ["Rwanda"],
    "STP": ["São Tomé and Príncipe", "Sao Tome and Principe"],
    "SEN": ["Senegal"],
    "SYC": ["Seychelles"],
    "SLE": ["Sierra Leone"],
    "SOM": ["Somalia"],
    "ZAF": ["South Africa"],
    "SSD": ["South Sudan"],
    "SDN": ["Sudan"],
    "TZA": ["Tanzania"],
    "TGO": ["Togo"],
    "UGA": ["Uganda"],
    "ZMB": ["Zambia"],
    "ZWE": ["Zimbabwe"]
}

# SSA Countries with ISOs only Arid regions
africa_arid_iso_countries_filtered = {
    "AGO": ["Angola"],
    "BEN": ["Benin"],
    "BWA": ["Botswana"],
    "BFA": ["Burkina Faso"],
    "BDI": ["Burundi"],
    "CMR": ["Cameroon"],
    "CAF": ["Central African Republic"],
    "TCD": ["Chad"],
    "CIV": ["Côte d'Ivoire", "CÃ´te d'Ivoire"],
    "COD": ["Democratic Republic of the Congo"],
    "DJI": ["Djibouti"],
    "ERI": ["Eritrea"],
    "SWZ": ["Eswatini", "Swaziland"],
    "ETH": ["Ethiopia"],
    "GMB": ["Gambia"],
    "GHA": ["Ghana"],
    "GIN": ["Guinea"],
    "KEN": ["Kenya"],
    "LSO": ["Lesotho"],
    "MDG": ["Madagascar"],
    "MWI": ["Malawi"],
    "MLI": ["Mali"],
    "MRT": ["Mauritania"],
    "MOZ": ["Mozambique"],
    "NAM": ["Namibia"],
    "NER": ["Niger"],
    "NGA": ["Nigeria"],
    "SEN": ["Senegal"],
    "SYC": ["Seychelles"],
    "SLE": ["Sierra Leone"],
    "SOM": ["Somalia"],
    "ZAF": ["South Africa"],
    "SSD": ["South Sudan"],
    "SDN": ["Sudan"],
    "TZA": ["Tanzania"],
    "TGO": ["Togo"],
    "UGA": ["Uganda"],
    "ZMB": ["Zambia"],
    "ZWE": ["Zimbabwe"]
}

# Full Africa countries with ISOs dictionary (includes North Africa)
africa_iso_countries = {
    **africa_iso_countries_filtered,  # Include all SSA countries
    "DZA": ["Algeria"],
    "CPV": ["Cape Verde", "Cabo Verde"],
    "EGY": ["Egypt"],
    "LBY": ["Libya"],
    "MAR": ["Morocco"],
    "MUS": ["Mauritius"],
    "TUN": ["Tunisia"]
}

# Define African regions using ISO codes from utility
regions_dict = {
    "Northern Africa": ["DZA", "EGY", "LBY", "MAR", "SDN", "TUN", "ESH"],
    "Southern Africa": ["BWA", "SWZ", "LSO", "NAM", "ZAF", "ZMB", "ZWE"],
    "East Africa": ["BDI", "COM", "DJI", "ERI", "ETH", "KEN", "MDG", "MWI", "MUS", "MYT", "MOZ", "REU", "RWA", "SYC", "SOM", "TZA", "UGA"],
    "West Africa": ["BEN", "BFA", "CPV", "CIV", "GMB", "GHA", "GIN", "GNB", "LBR", "MLI", "MRT", "NER", "NGA", "SEN", "SLE", "TGO"],
    "Central Africa": ["AGO", "CMR", "CAF", "TCD", "COG", "GNQ", "GAB", "COG", "STP"]
}

# ISO code lists for easy access
ssa_iso = list(africa_iso_countries_filtered.keys())
africa_iso = list(africa_iso_countries.keys())
region_names = list(regions_dict.keys())