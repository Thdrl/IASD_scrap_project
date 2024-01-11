import requests
import json
import psycopg2
import ast

from utils import batch_insert, get_db_params, get_or_create_id, insert_line
from lidl.process_lidl import process_line as process_lidl_line
from openrecipes_dump.process_openrecipes import process_line as process_openrecipes_line

db_params = get_db_params()

conn = psycopg2.connect(db_params)
cursor = conn.cursor()

#insert lidl
json_file_path = 'lidl/output.json'
with open(json_file_path) as f:
    recipes_batch = []
    for line in f:
        processed_line = process_lidl_line(line)
        #ensure recipe has the right data
        recipe_data = {key: processed_line.get(key) for key in ['name', 'source', 'url', 'image', 'servings', 'time', 'difficulty', 'instructions']}

        insert_line(cursor, processed_line, recipe_data) 

        #commit
        conn.commit()

#insert openrecipes 
json_file_path = 'openrecipes/openrecipes.json'
with open(json_file_path) as f:
    batch = []
    for line in f:
        line = ast.literal_eval(line)
        processed_line = process_openrecipes_line(line)
        #ensure recipe has the right data
        recipe_data = {key: processed_line.get(key) for key in ['name', 'source', 'url', 'image', 'servings', 'time', 'difficulty', 'instructions']}

        insert_line(cursor, processed_line, recipe_data) 

        #commit
        conn.commit()
        

# Close communication with the database
cursor.close()
conn.close()