import os
data_loc = '/home/waves/data/Africa_Irrigation/Data'

# Download and unpack the dam data to the cluster

dam_url = "https://sedac.ciesin.columbia.edu/downloads/data/grand-v1/grand-v1-dams-rev01/dams-rev01-global-shp.zip"

# Create the directory if it doesn't exist
raw_data_dir = os.path.join(data_loc, 'anna', 'raw')
os.makedirs(raw_data_dir, exist_ok=True)

# Download the dam data zip file
zip_file_path = os.path.join(raw_data_dir, 'dams-rev01-global-shp.zip')

############################################################################################################
# For some reason this code doesn't work so I downloaded and unzipped the file manually on my local machine and moved it over using FileZilla

# urllib.request.urlretrieve(dam_url, zip_file_path)

# # Unzip the file
# with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
#     zip_ref.extractall(raw_data_dir)

# # Remove the zip file
# os.remove(zip_file_path)
############################################################################################################