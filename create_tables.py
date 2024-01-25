import psycopg2
from psycopg2 import sql

from utils import get_db_params

# Database connection parameters
db_params = get_db_params()
conn = psycopg2.connect(**db_params)
cur = conn.cursor()

# SQL statements to create tables
create_commands = (
    """
    CREATE TABLE IF NOT EXISTS Recipes (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255),
        source VARCHAR(255),
        url TEXT,
        image TEXT,
        servings INT,
        time INT,
        difficulty VARCHAR(50),
        category VARCHAR(255),
        instructions TEXT
    )
    """,
    """ 
    CREATE TABLE IF NOT EXISTS Ingredients (
        IngredientID SERIAL PRIMARY KEY,
        Name VARCHAR(255) NOT NULL UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS RecipeIngredients (
        RecipeID INT NOT NULL,
        IngredientID INT NOT NULL,
        Quantity DECIMAL,
        Unit VARCHAR(50),
        FOREIGN KEY (RecipeID)
            REFERENCES Recipes (id)
            ON UPDATE CASCADE ON DELETE CASCADE,
        FOREIGN KEY (IngredientID)
            REFERENCES Ingredients (IngredientID)
            ON UPDATE CASCADE ON DELETE CASCADE,
        PRIMARY KEY (RecipeID, IngredientID)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS Categories (
        CategoryID SERIAL PRIMARY KEY,
        Name VARCHAR(255) NOT NULL UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS RecipeCategories (
        RecipeID INT NOT NULL,
        CategoryID INT NOT NULL,
        FOREIGN KEY (RecipeID)
            REFERENCES Recipes (id)
            ON UPDATE CASCADE ON DELETE CASCADE,
        FOREIGN KEY (CategoryID)
            REFERENCES Categories (CategoryID)
            ON UPDATE CASCADE ON DELETE CASCADE,
        PRIMARY KEY (RecipeID, CategoryID)
    )
    """
)

drop_commands = (
    "DROP TABLE IF EXISTS RecipeCategories CASCADE",
    "DROP TABLE IF EXISTS Categories CASCADE",
    "DROP TABLE IF EXISTS RecipeIngredients CASCADE",
    "DROP TABLE IF EXISTS Ingredients CASCADE",
    "DROP TABLE IF EXISTS Recipes CASCADE"
)

for command in drop_commands:
    cur.execute(command)
conn.commit()
print("Existing tables deleted.")

for command in create_commands:
    cur.execute(command)
conn.commit()
print("Tables created.")

# Close communication with the database
cur.close()
conn.close()