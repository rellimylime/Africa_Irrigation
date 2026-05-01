import os
import ast

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - fallback when PyYAML is unavailable
    yaml = None

# Locate config.yaml relative to this file (project root), not relative to CWD.
# This means load_config/resolve_path work regardless of where notebooks are run from.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_config = None


def _parse_simple_yaml(text):
    """Parse the repository's simple key/value config without PyYAML.

    This fallback supports the config layout used in this repo:
    - one ``key: value`` pair per line
    - quoted strings
    - booleans, numbers, and ``null``-like values
    - full-line and trailing comments
    """
    config = {}

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue

        if "#" in value:
            value = value.split("#", 1)[0].rstrip()

        if not value:
            config[key] = None
            continue

        try:
            config[key] = ast.literal_eval(value)
        except Exception:
            lowered = value.lower()
            if lowered in {"null", "none", "~"}:
                config[key] = None
            elif lowered == "true":
                config[key] = True
            elif lowered == "false":
                config[key] = False
            else:
                config[key] = value

    return config

def load_config():
    global _config
    if _config is None:
        with open(os.path.join(_REPO_ROOT, 'config.yaml'), 'r', encoding='utf-8') as f:
            text = f.read()
        if yaml is not None:
            _config = yaml.safe_load(text)
        else:
            _config = _parse_simple_yaml(text)
    return _config

def resolve_path(relative_path):
    """Resolve a config-relative path to an absolute path using base_path."""
    return os.path.join(load_config()['base_path'], relative_path)

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
    "Central Africa": ["AGO", "CMR", "CAF", "TCD", "COG", "GNQ", "GAB", "STP"]
}

# ISO code lists for easy access
ssa_iso = list(africa_iso_countries_filtered.keys())
africa_iso = list(africa_iso_countries.keys())
region_names = list(regions_dict.keys())
