from pathlib import Path
import re
import os
import json
import re
import unidecode
from collections import Counter
from itertools import chain

##YIELD CLEANING

def clean_yield(field):
    #returns the yield field as an integer, or None if no pattern found
    if field is None:
        return None
    
    # Extract all numbers from the string
    numbers = re.findall(r'\b\d+\b', field)

    if len(numbers) == 1:
        # Single number
        num = int(numbers[0])
        return num if num < 13 else None
    elif len(numbers) == 2:
        # Two numbers - calculate the average
        num1, num2 = map(int, numbers)
        avg = (num1 + num2) / 2
        return int(avg) if avg < 13 else None
    else:
        # No numbers or pattern not matched
        return None


##TIME CLEANING


def time_to_min(time_str):
    #turns the db format PTHM into minutes
    if time_str is None:
        return None
    # Extract hours and minutes using regular expression
    match = re.match(r'PT(\d+H)?(\d+M)?', time_str)
    if not match:
        return None

    hours, minutes = match.groups()

    # Convert hours and minutes to integers
    total_minutes = 0
    if hours:
        total_minutes += int(hours[:-1]) * 60  # Remove 'H' and convert to minutes
    if minutes:
        total_minutes += int(minutes[:-1])     # Remove 'M'
    
    if total_minutes == 0:
        return None
    
    return total_minutes

def get_clean_time(line):
    #returns a single time (mn) value for the recipe line
    prepTime = line['prepTime']
    cookTime = line['cookTime']
    totalTime = line['totalTime']

    prepTime = time_to_min(prepTime)
    cookTime = time_to_min(cookTime)
    totalTime = time_to_min(totalTime)

    if ((prepTime is not None) and (cookTime is not None)) and totalTime is None:
        totalTime = prepTime + cookTime
    elif (prepTime is not None) and (cookTime is None):
        totalTime = prepTime
    elif (prepTime is None) and (cookTime is not None):
        totalTime = cookTime

    return totalTime


##INGREDIENTS CLEANING


def remove_leading(text):
    prefixes = ['.25oz ', '.5oz ', '.75oz ', '.5fl oz ', '/½ ', '/¼ ', 'of ', '¼oz ', '¼ oz ','½oz ', '½ oz ', 'oz ', '1oz ', '1 oz ', '2oz ', '2 oz ', '1/2 oz ', '1/2oz ',  '3oz ', '3 oz ', '4oz ', '4 oz ', '5oz ', '5 oz ', '6oz ', '6 oz ', '7oz ', '7 oz ', '8oz ', '8 oz ', '9oz ', '9 oz ', '10oz ', '10 oz ',' ','. ']
    for prefix in prefixes:
        if text.startswith(prefix):
            return text[len(prefix):]
    return text

def unicode_to_float(frac_str):
    # Convert vulgar fractions like ½ to floats like 0.5
    vulgar_fracs = {
        '½': 0.5,
        '⅓': 0.3333,
        '⅔': 0.6666,
        '¼': 0.25,
        '¾': 0.75
    }
    return vulgar_fracs.get(frac_str, frac_str)

def strfrac_to_float(frac_str):
    # Convert string fractions like '1/2' to floats like 0.5
    if '/' not in frac_str:
        return float(frac_str)
    num, denom = frac_str.split('/')
    return float(num) / float(denom)

def add_floats_match(match):
    # Convert the matched group to a float
    int_nb = int(match.group(1))
    frac_nb = unicode_to_float(match.group(2))
    if isinstance(frac_nb, float):
        return str(int_nb + frac_nb)
    else:
        return match.group(0)

def is_repeating(ingredient_str):
    pattern = re.compile(r'(\b[\S\s]+?\b)(?:\s+\1\b|\n\s*\1\b)')
    return pattern.match(ingredient_str) is not None   

def parse_ingredient(ingredient_str):
    #returns a tuple (quantity, unit, ingredient) from a crude str
    if is_repeating(ingredient_str):
        return (None, None, None)
    
    # Check if the string is fully alphabetic
    if ingredient_str.replace(" ", "").isalpha():
        return (None, None, ingredient_str)

    # Convert leading vulgar fraction to a float
    clean_str = re.sub(r'^([½⅓⅔¼¾])\s*', lambda m: str(unicode_to_float(m.group(1))), ingredient_str)

    # Remove any leading non-numeric text
    clean_str = re.sub(r'^[^\d]+', '', clean_str)

    # Handle combined numbers like "4 ½" or "2¾"
    clean_str = re.sub(r'(\d+)\s*+(½|⅓|⅔|¼|¾|\d+/\d+)', add_floats_match, clean_str)

    # Pattern for fractional quantities like "½ tsp salt"
    pattern_fractional = r'([^\d\s]*\s*\d+/\d+|[^\d\s]+)\s*([a-zA-Z]+)\s*(.*)'
    # Pattern for quantities with units like "250g/9oz butter"
    pattern_dual_unit = r'\b(\d+\.?\d*)\s*([a-zA-Z]+)(?:\/\d+\s*[a-zA-Z]*)?\s*(.*)'

    # Try matching the fractional pattern
    match = re.match(pattern_fractional, clean_str.strip())
    if match:
        value, unit, ingredient = match.groups()
        return (strfrac_to_float(value), unit, remove_leading(ingredient))

    # Try matching the dual unit pattern
    match = re.match(pattern_dual_unit, clean_str.strip())
    if match:
        value, unit, ingredient = match.groups()
        return (strfrac_to_float(value), unit, remove_leading(ingredient))

    # Return None, None, ingredient if no pattern matches
    return (None, None, ingredient_str)


#Obtained from listing all the uniques units from parsed ingredients ranked by frequency

valid_unit_list = ['g',
 'tbsp',
 'tsp',
 'cup',
 'ml',
 'teaspoon',
 'cups',
 'tablespoon',
 'Tb',
 'tablespoons',
 'Tablespoons',
 'teaspoons',
 'ounces',
 'oz',
 'sprigs',
 'slices',
 'Tablespoon',
 'clove',
 'kg',
 'sprig',
 'pound',
 'cm',
 'stick',
 'spring',
 'sticks',
 'litre',
 'can',
 'lb',
 'litres',
 'ounce',
 'pinch',
 'pounds',
 'handful',
 'lbs',
 'cans',
 'jar',
 'pint',
 'fennel',
 'bottle',
 'Tbsp',
 'grams',
 'Tbs',
 'L',
 'lbs']

def normalize_unit(unit):
    unit_mapping = {
        'tablespoon': 'tbsp',
        'Tablespoon': 'tbsp',
        'Tablespoons': 'tbsp',
        'tablespoons': 'tbsp',
        'Tb': 'tbsp',
        'Tbs': 'tbsp',
        'Tbsp': 'tbsp',
        'teaspoon': 'tsp',
        'teaspoons': 'tsp',
        'cup': 'cups',
        'milliliters': 'ml',
        'litre': 'L',
        'litres': 'L',
        'ounce': 'oz',
        'ounces': 'oz',
        'kilograms': 'kg',
        'pound': 'lb',
        'pounds': 'lb',
        'lbs': 'lb',
        'centimeters': 'cm',
        'stick': 'sticks',
        'sprig': 'sprigs',
        'can': 'cans',
        'pinch': 'pinches',
        'handful': 'handfuls',
        'jar': 'jars',
        'pint': 'pints',
        'grams': 'g'
    }
    return unit_mapping.get(unit, unit)

def group_ingredients(ingredient): 
    if 'butter' in ingredient:
        return 'butter'
    if 'eggs' in ingredient or 'egg' in ingredient:
        return 'eggs'
    if 'flour' in ingredient:
        return 'flour'
    if 'caster sugar' in ingredient:
        return 'sugar'
    if 'mint' in ingredient:
        return 'mint'
    if 'parsley' in ingredient:
        return 'parsley'
    
    
    return ingredient

def clean_ingredient(ingredients_str):
    """
    Returns a cleaned ingredients : 
    1. parsing to tuple (quantity, unit, ingredient)
    2. normalized units, grouped ingredients, removed duplicates
    """
    ingredients = ingredients_str.split('\n')[1:]
    quantities, units, names = [], [], []
    for ingredient in ingredients:
        
        quantity, unit, name = parse_ingredient(ingredient)
        if quantity is None:
            continue
        quantities.append(quantity)

        if unit not in valid_unit_list:
            name = unit + ' ' + name
            unit = None
        else:
            unit = normalize_unit(unit)   
        units.append(unit)

        name = name.strip()
        name = group_ingredients(name)
        names.append(name)

    return quantities, units, names

## CATEGORIES

def normalize_categ(category):
    category.strip()
    category = category.lower()

    if ("main" in category) or ("dinner" in category) or ('lunch' in category):
        return "main"
    if ("cookie" in category) or ('dessert' in category) or ('cake' in category):
        return "dessert"
    if "side" in category:
        return "side dish"
    if "appetizer" in category:
        return "appetizer"
    if "soup" in category:
        return "soup"
    if "water" in category:
        return "water"
    
    return category

def clean_translated_ingredients(translated_ings):
    clean = []
    for ing in translated_ings:
        #remove accents
        ing = unidecode.unidecode(ing)
        #remove capital letters 
        ing = ing.lower()
        #remove 'de ', "l' ", 'du ', 'des ', "d' ", 'le ', 'les ' if leading
        for prefix in ['de ', "l'", 'du ', 'des ', "d'", 'le ', 'les ']:
            if ing.startswith(prefix):
                ing = ing[len(prefix):]
        #oe
        ing = re.sub(r'œ', 'oe', ing)
        clean.append(ing)
        #dele
    return clean

##UNIT CONVERSION

def translation_unit_mapping(english_unit):
    translation_map = {
        None: None,
        'g': 'g',
        'ml': 'ml',
        'tbsp': 'c. a s.',
        'tsp': 'c. a c.',
        'cans': 'boites',
        'sticks': 'batonnets',
        'clove': 'gousse',
        'jars': 'pots',
        'slices': 'tranches',
        'bottle': 'bouteille',
        'cm': 'cm',
        'sprigs': 'brins',
        'L': 'L',
        'pinches': 'pincees',
        'kg': 'kg',
        'fennel': 'fenouil',
        'handfuls': 'poignees',
    }
    return translation_map.get(english_unit, english_unit)

def uncommon_ingredient(ingredient, common_ingredients):
    return ingredient not in common_ingredients

def convert_to_metric(value, unit):
    conversion_factors = {
        'cups': {'factor': 236.588, 'metric_unit': 'ml'},
        'oz': {'factor': 28.3495, 'metric_unit': 'g'},
        'lb': {'factor': 453.592, 'metric_unit': 'g'},
        'pints': {'factor': 473.176, 'metric_unit': 'ml'},
    }
    if unit in conversion_factors:
        factor = conversion_factors[unit]['factor']
        metric_unit = conversion_factors[unit]['metric_unit']
        return value * factor, metric_unit
    else:
        return value, unit

def get_difficulty_from_nb_ingredients(nb_ingredients):
    if nb_ingredients <= 5:
        return '1'
    elif nb_ingredients <= 10:
        return '2'
    else:
        return '3'




## GET COMMON INGREDIENTS

ingredients = list(chain.from_iterable([clean_ingredient(line['ingredients'])[2] for line in lines]))
counts = Counter(ingredients)
print(counts.most_common(200))
#200 most common ingredients in a list 
common_ingredients = [ing for ing,ct in counts.most_common(200)]


## TRANSLATION
common_categories = ['breakfast', 'main', 'dessert', 'appetizer', 'soup', 'bread', 'miscellaneous', 'salad', 'snack', 'side dish']
#semi hand-made
translated_categories = ['petit déjeuner', 'plat', 'dessert', 'appéritif', 'soupe', 'pain', 'divers', 'salade', 'gouter', 'accompagnement']


LANG = 'fr' #or 'en'
translate_ing = True

import deepl

auth_key = 'x'
translator = deepl.Translator(auth_key)
if translate_ing:       
    translated_ingredients = []
    for ingredient in common_ingredients:
        if len(ingredient) > 0:
            translated_ingredients.append(translator.translate_text(ingredient, target_lang='FR').text)


translated_ingredients = clean_translated_ingredients(translated_ingredients)

##MAIN FUNC

def process_line(line):
        #get raw data
        raw_ingredients = line.get('ingredients')
        recipeYield = line.get('recipeYield')
        prepTime = line.get('prepTime')
        url = line.get('url')
        image = line.get('image')
        totalTime = line.get('totalTime')
        cookTime = line.get('cookTime')
        name = line.get('name') 
        source = line.get('source')
        category = line.get('recipeCategory')
        
        #process data
        ingredient_values, ingredient_units, ingredients = clean_ingredients(raw_ingredients)
        if any(ingredient is None for ingredient in ingredients):
            continue

        difficulty = get_difficulty_from_nb_ingredients(len(ingredients))
        time = get_clean_time(line)
        if source is None:
            source = 'openrecipes'
        recipeYield = clean_yield(recipeYield)

        #convert to metric system
        for i, value in enumerate(ingredient_values):
            ingredient_values[i], ingredient_units[i] = convert_to_metric(value, ingredient_units[i])


            #delete 
            if ingredient_units[i] not in unique_units:
                unique_units.append(ingredient_units[i])



        if category not in common_categs:
            category = None

        #deletion checks
        if time is None:
            continue
        if int(time) > 240:
            continue
        if (len(ingredients) > 25) or (len(ingredients) < 3):
            continue
        if recipeYield is None:
            continue
        if any(uncommon_ingredient(ingredient, common_ingredients) for ingredient in ingredients):
            continue
        # if list(set(ingredients)) != ingredients:
        #     continue
        
        #translate ingredients to french if LANG == 'fr'
        assert LANG in ['fr', 'en']
        if LANG == 'fr':
            #make the french translation by mapping the id between ingredients and translated_ingredients
            ingredients = [translated_ingredients[common_ingredients.index(ingredient)] for ingredient in ingredients]
            if category is not None:
                category = translated_categories[common_categs.index(category)]
            #translate units
            ingredient_units = [translation_unit_mapping(unit) for unit in ingredient_units]


        return {
            'name': name,
            'source': source,
            'category': category,
            'url': url,
            'image': image,
            'servings': recipeYield,
            'time': time,
            'difficulty': difficulty,
            'ingredients': ingredients,
            'ingredient_values': ingredient_values,
            'ingredient_units': ingredient_units
        }