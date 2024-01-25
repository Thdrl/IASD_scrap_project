import psycopg2
import ast
import json
import os
import tqdm

from utils import get_db_params, insert_line, get_lines
from lidl.process_lidl import process_line as process_lidl_line
from openrecipes_dump.process_openrecipes import process_line as process_openrecipes_line
from openrecipes_dump.process_openrecipes import get_ingredients_and_translate


db_params = get_db_params()
conn = psycopg2.connect(**db_params)
cursor = conn.cursor()



# #insert lidl
json_file_path = 'lidl/output.json'
if not os.path.exists(json_file_path):
    raise Exception('File '+ json_file_path +' does not exist')

with open(json_file_path, 'r', encoding='utf-8') as file:
    lines = json.load(file)
    for line in lines: #tqdm.tqdm(file, total=len(lines), desc="Processing LIDL lines"):
        processed_line = process_lidl_line(line)
        #ensure right data formats for db
        recipe_data = {key: processed_line.get(key) for key in ['name', 'source', 'url', 'image', 'servings', 'time', 'difficulty', 'instructions']}
        ingredients_data = {key: processed_line.get(key) for key in ['ingredients', 'ingredients_values', 'ingredients_units']}
        category = processed_line.get('category')

        insert_line(cursor, recipe_data, ingredients_data, category) 

        #commit
        conn.commit()
    print('loaded '+ str(len(lines)) +' lidl recipes into db')

#insert openrecipes 
json_file_path = 'openrecipes_dump/openrecipes.json'
if not os.path.exists(json_file_path):
    raise Exception('File '+ json_file_path +' does not exist')

with open(json_file_path, 'r', encoding='utf-8') as file:
    n_lines = get_lines(file)
    n_skipped = 0
    reasons = {'literal_eval': 0, 'misstime': 0, 'longtime': 0, 'nb_ingredients': 0, 'missyield': 0, 'uncommon_ingredient': 0, 'translation': 0}

    common_ings, translated_ings = get_ingredients_and_translate(file)
    for line in tqdm.tqdm(file, total=n_lines, desc="Processing OPENRECIPES lines"):
        try:
            line = ast.literal_eval(line)
        except ValueError:
            n_skipped += 1
            reasons['literal_eval'] += 1
            continue

        processed_line, reason = process_openrecipes_line(line, common_ings, translated_ings)

        #if returned None, skip the line
        if not processed_line:
            n_skipped += 1
            reasons[reason] += 1
            continue

        #ensure recipe has the right data
        recipe_data = {key: processed_line.get(key) for key in ['name', 'source', 'url', 'image', 'servings', 'time', 'difficulty', 'instructions']}
        ingredients_data = {key: processed_line.get(key) for key in ['ingredients', 'ingredients_values', 'ingredients_units']}
        category = processed_line.get('category')

        insert_line(cursor, recipe_data, ingredients_data, category)  

        #commit
        conn.commit()

    print('loaded '+ str(n_lines - n_skipped) +' openrecipes recipes into db, accepted '+ str(round((1 - n_skipped/n_lines)*100, 2)) +' percent of lines')
    print('skipped '+ str(n_skipped) +' lines for the following reasons:')
    print(reasons)
        

# Close communication with the database
cursor.close()
conn.close()

