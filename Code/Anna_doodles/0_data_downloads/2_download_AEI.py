import os
import urllib
data_loc = '/home/waves/data/Africa_Irrigation/Data'
raw_data_dir = os.path.join(data_loc, 'anna', 'raw')

# Download all irrigation data starting in 1980 -- takes about 2.5 minutes

years = range(1980, 2016, 5)

# Make an AEI folder
aei_dir = os.path.join(raw_data_dir, 'AEI')
os.makedirs(aei_dir, exist_ok=True)


# Download all MEIER data
for year in years:
    url = f"https://zenodo.org/record/7809342/files/MEIER_G_AEI_{year}.ASC?download=1"
    file_path = os.path.join(aei_dir, f"MEIER_G_AEI_{year}.ASC")
    urllib.request.urlretrieve(url, file_path)

# Download all Mehta data
for year in years:
    url = f"https://zenodo.org/record/7809342/files/G_AEI_{year}.ASC?download=1"
    file_path = os.path.join(aei_dir, f"G_AEI_{year}.ASC")
    urllib.request.urlretrieve(url, file_path)