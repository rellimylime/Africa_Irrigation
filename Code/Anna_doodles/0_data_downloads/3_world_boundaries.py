
import os
import urllib
import zipfile
data_loc = '/home/waves/data/Africa_Irrigation/Data'
raw_data_dir = os.path.join(data_loc, 'anna', 'raw')


# Download country boundaries
world_boundaries_url = "https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets/world-administrative-boundaries/exports/shp?lang=en&timezone=America%2FLos_Angeles"

# Create the directory if it doesn't exist
world_boundaries_path = os.path.join(raw_data_dir, 'world_boundaries')
os.makedirs(world_boundaries_path, exist_ok=True)
world_boundaries_path = os.path.join(world_boundaries_path, 'world_boundaries.zip')

urllib.request.urlretrieve(world_boundaries_url, world_boundaries_path)

# Unzip the file
with zipfile.ZipFile(world_boundaries_path, 'r') as zip_ref:
    zip_ref.extractall(raw_data_dir)

# Remove the zip file
os.remove(world_boundaries_path)