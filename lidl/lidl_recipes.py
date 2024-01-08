import requests
import xml.etree.ElementTree as ET

## Get the urls of all the recipes on the website from the sitemap

sitemap = requests.get('https://www.lidl-recettes.fr/sitemap.xml') # Get the sitemap
sm_xml = ET.fromstring(sitemap.content) # Parse the sitemap       

recipe_urls = []
for child in sm_xml:
    if '/recettes/' in child[0].text:  
        recipe_urls.append(child[0].text) # Get the url of each recipe

recipe_names = [url.split('/')[-1] for url in recipe_urls] # Get the name of each recipe
#print(recipe_names)


## Get the ingredients of each recipe

root_url = 'https://www.lidl-recettes.fr/recettes/' # The root for recipes

# Write the full URL for all recipes in a JSON file
with open('lidl_recipes.json', 'w') as file:
    file.write('[')
    for i, url in enumerate(recipe_urls):
        file.write(f'"{root_url}{recipe_names[i]}"')
        if i != len(recipe_urls)-1:
            file.write(',\n')
    file.write(']')
    
     