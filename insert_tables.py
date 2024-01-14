import psycopg2
import ast
import json
import os

from utils import get_db_params, insert_line
from lidl.process_lidl import process_line as process_lidl_line
from openrecipes_dump.process_openrecipes import process_line as process_openrecipes_line
from openrecipes_dump.process_openrecipes import get_ingredients_and_translate


db_params = get_db_params()
conn = psycopg2.connect(**db_params)
cursor = conn.cursor()

#insert lidl
json_file_path = 'lidl/output.json'
if not os.path.exists(json_file_path):
    raise Exception('File '+ json_file_path +' does not exist')

with open(json_file_path, 'r', encoding='utf-8') as file:
    lines = json.load(file)
    for line in lines:
        processed_line = process_lidl_line(line)
        assert len(processed_line['ingredients']) == len(processed_line['ingredients_values']) == len(processed_line['ingredients_units'])
        #ensure recipe has the right data
        recipe_data = {key: processed_line.get(key) for key in ['name', 'source', 'url', 'image', 'servings', 'time', 'difficulty', 'instructions']}

        insert_line(cursor, processed_line, recipe_data) 

        #commit
        conn.commit()
    print('loaded lidl recipes into db')

#insert openrecipes 
json_file_path = 'openrecipes/openrecipes.json'
if not os.path.exists(json_file_path):
    raise Exception('File '+ json_file_path +' does not exist')

with open(json_file_path, 'r') as f:
    common_ings, translated_ings = get_ingredients_and_translate(f)
    for line in f:
        line = ast.literal_eval(line)
        processed_line = process_openrecipes_line(line, common_ings, translated_ings)
        #ensure recipe has the right data
        recipe_data = {key: processed_line.get(key) for key in ['name', 'source', 'url', 'image', 'servings', 'time', 'difficulty', 'instructions']}

        insert_line(cursor, processed_line, recipe_data) 

        #commit
        conn.commit()
    print('loaded openrecipes recipes into db')
        

# Close communication with the database
cursor.close()
conn.close()

