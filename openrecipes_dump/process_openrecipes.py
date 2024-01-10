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

auth_key = '9093d919-3022-b8c7-19ba-93ceff08f8d7:fx'
translator = deepl.Translator(auth_key)
if translate_ing:       
    translated_ingredients = []
    for ingredient in common_ingredients:
        if len(ingredient) > 0:
            translated_ingredients.append(translator.translate_text(ingredient, target_lang='FR').text)



##MAIN FUNC

def process_line(line):
    




    return line 