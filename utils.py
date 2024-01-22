import json

def get_db_params():
    return {
    'dbname': 'recipe_db',
    'user': 'postgres',
    'password': 'password',
    'host': 'localhost'
    }

def get_or_create_id(cursor, table, column, value):
    if table == 'Categories':
        table_id = 'CategoryID'
    else:
        table_id = f'{table[:-1]}ID'

    cursor.execute(f"SELECT {table_id} FROM {table} WHERE {column} = %s", (value,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        cursor.execute(f"INSERT INTO {table} ({column}) VALUES (%s) RETURNING {table_id}", (value,))
        # cursor.execute(f"""
        #     INSERT INTO {table} ({column}) VALUES (%s)
        #     ON CONFLICT ({column}) DO UPDATE SET {column} = EXCLUDED.{column}
        #     RETURNING {table_id}
        #     """, (value,))
        return cursor.fetchone()[0]
    

def insert_line(cursor, recipe_data, ingredients_data, category):
    #insert and get recipe id
        cursor.execute("INSERT INTO Recipes (name, source, url, image, servings, time, difficulty, instructions) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
                        (recipe_data['name'], recipe_data['source'], recipe_data['url'], recipe_data['image'], recipe_data['servings'], recipe_data['time'], recipe_data['difficulty'], recipe_data['instructions']))
        recipe_id = cursor.fetchone()[0]
        recipe_inserted = True

        #recipe_ingredients & ingredients population
        for i, ingredient in enumerate(ingredients_data['ingredients']):
            ingredient_id = get_or_create_id(cursor, 'Ingredients', 'Name', ingredient)
            cursor.execute("INSERT INTO RecipeIngredients (RecipeID, IngredientID, Quantity, Unit) VALUES (%s, %s, %s, %s) ON CONFLICT (RecipeID, IngredientID) DO NOTHING",
                        (recipe_id, ingredient_id, ingredients_data['ingredients_values'][i], ingredients_data['ingredients_units'][i]))
                
        #category data
        if category:
            category_id = get_or_create_id(cursor, 'Categories', 'Name', category)
            cursor.execute("INSERT INTO RecipeCategories (RecipeID, CategoryID) VALUES (%s, %s)ON CONFLICT (RecipeID, CategoryID) DO NOTHING",
                           (recipe_id, category_id))



def get_lines(f):
    f.seek(0)
    n_lines = sum(1 for line in f)
    f.seek(0)
    return n_lines