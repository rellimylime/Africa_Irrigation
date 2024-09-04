import os
import inspect
import yaml

# Access to project base_path
def load_config():
    with open('../../config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    return config

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


    