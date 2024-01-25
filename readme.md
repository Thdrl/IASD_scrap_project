# Cooking Idea Database

## Description
This project is a database of cooking ideas. It is designed to provide users with a variety of cooking recipes and meal ideas. They can for eexample query the database with a list of ingredients they have at hand and the database can return a list of meals they can prepare. \\

The data is taken from multiple sources :
- LIDL recipe website : https://www.lidl-recettes.fr 4000+ well detailed professional and easy recipes from french cuisine (scrapping)
- OpenRecipes : https://github.com/fictivekin/openrecipes 170K+ recipes from users around the world, especially america (JSON dump)

other sources were considered and could be implemented in a future version :
- RecipeNLG Kaggle dataset : https://www.kaggle.com/datasets/paultimothymooney/recipenlg 1M+ cooking recipes (CSV)
- TheMealDB : https://www.themealdb.com/api.php cooking recipes from around the world (API access)

The database is made with psycopg2 postgresql python interface...



## Data quality

The database being intended for french speaking users, the ingredients in english were translated to get the best overlap between the 2 sources...

Since it is of very high quality, the data from LIDL had very few processing, and all entries were logged in the database. Without the (very few) process-passing lines that were not inserted at the SQL level through UPSERT, the % of accepted lines from the openrecipes json was initially 0.98%. Since this is too low even for a low quality dataset, we play on the processing parameters :

- nb. of ingredients : Before iterating over the lines, the code finds the n most common ingredients in the file and keeps only the recipes with all ingredients in the common ones. With 250: 0.98%, 500: 1.56%, 1000: 2.44%, 2500: 3.87%. We keep 1000 as it is close to the number of ingredients from the other data.

For the other parameters, we log the reason of exclusion in the process_line function. The entry deletion checks skipped 169043 (97%) lines with the following stats:

- ingredient not in common list: 84894
- too many (>25) or few (<3) ingredients: 49914
- literal_eval error : 27247
- time missing : 3792
- time above 240mn: 2510
- yield missing: 686
- translation issue: 4


{'literal_eval': 27247, 'misstime': 3792, 'longtime': 2510, 'nb_ingredients': 49914, 'missyield': 686, 'uncommon_ingredient': 84894, 'translation': 4}

Note: since the checks are done sequentially, it does not represent the % of lines with the above problems.

Since the data quality is important, the checks stay as is, especially considering the database was user-generated.

## Tests on the db


## Usage
Usage examples are provided in the ```examples.ipynb``` notebook. 

## Next steps

### Code improvements :
- Apart from adding new data sources, the code for the openrecipes source could be adapted to be able to feed from different sources with the same code, allowing for easier expansion of the database.

- The ingredients-based filtering method relying on only keeping the recipes with ingredients in the $n$ most common ones in the db is harsh on the data, excluding around half of it. Furthermore, getting the common ingredients & translating them is memory-intensive as it searches through the whole data. 

- Duplicates handling : as of now, no duplicate handling is in the code, this could become crucial if more data sources are added to the pipeline.

- Profiling and optimization to reduce runtime for unclean data sources like openrecipes.

### Real use-case
One possible application is a "build-a-meal" tool, which could use AI to analyze a photo of the contents of a refrigerator. This application would identify the ingredients and their quantities, and then suggest recipes based on various criteria using the available items.