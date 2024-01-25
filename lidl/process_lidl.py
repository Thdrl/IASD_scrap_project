from pathlib import Path
import re
import os
import json
import re
import unidecode

def clean_french(string):
    if string is None:
        return None 
    string = unidecode.unidecode(string)
    string = string.lower()
    string = re.sub(r'œ', 'oe', string)
    # Replace 'LINE SEPARATOR' with space
    string = re.sub(r'\u2028', ' ', string) 
    return string

def process_line(line):
    line['ingredients'] = [clean_french(ingredient) for ingredient in line['ingredients']]
    line['title'] = clean_french(line['title'])
    line['category'] = clean_french(line['category'])
    #replace key title with name
    line['name'] = line.pop('title')
    return line