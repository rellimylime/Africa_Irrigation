import os
import inspect
import yaml

# Access to project base_path
def load_config():
    #config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    with open('../../config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    return config

def make_output_path(file_name):

    return os.path.join((load_config())['base_path'], 'Output' )
    