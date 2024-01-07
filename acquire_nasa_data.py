# Script for gathering data from the EONET NASA API
# see https://eonet.sci.gsfc.nasa.gov/docs/v2.1

import json

with open('nasa_data.json', 'r') as file:
    data = json.load(file)

filtered_data = []

