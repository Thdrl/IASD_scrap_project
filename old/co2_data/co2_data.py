# Script for the CO2 world data from https://github.com/owid/co2-data

import json

with open('owid-co2-data.json', 'r') as file:
    data = json.load(file)

filtered_data = []

