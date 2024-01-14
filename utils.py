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
        return cursor.fetchone()[0]
    

def insert_line(cursor, processed_line, recipe_data):
    #insert and get recipe id
        cursor.execute("INSERT INTO Recipes (name, source, url, image, servings, time, difficulty, instructions) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
                        (recipe_data['name'], recipe_data['source'], recipe_data['url'], recipe_data['image'], recipe_data['servings'], recipe_data['time'], recipe_data['difficulty'], recipe_data['instructions']))
        recipe_id = cursor.fetchone()[0]

        #recipe_ingredients & ingredients population
        for i, ingredient in enumerate(processed_line['ingredients']):
            ingredient_id = get_or_create_id(cursor, 'Ingredients', 'Name', ingredient)
            cursor.execute("INSERT INTO RecipeIngredients (RecipeID, IngredientID, Quantity, Unit) VALUES (%s, %s, %s, %s)",
                        (recipe_id, ingredient_id, processed_line['ingredients_values'][i], processed_line['ingredients_units'][i]))
        
        #category data
        if processed_line['category']:
            category_id = get_or_create_id(cursor, 'Categories', 'Name', processed_line['category'])
            cursor.execute("INSERT INTO RecipeCategories (RecipeID, CategoryID) VALUES (%s, %s)", (recipe_id, category_id))