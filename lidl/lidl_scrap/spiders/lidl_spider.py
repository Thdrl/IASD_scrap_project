import scrapy
from pathlib import Path
import re
from unidecode import unidecode
import os
import json

def clean_instructions(instructions):
    cleaned_text = ""
    print(instructions)
    print( '\n\n\n\n\n\n')
    
    for instruction in instructions:
        # Strip leading/trailing whitespace
        instruction = str(instruction).strip()
        
        # Check if the current cleaned_text ends with a period
        if cleaned_text.endswith('.'):
            # Add a newline if the instruction is complete
            cleaned_text += " \n"
        else:
            # Add a space if the instruction is ongoing
            cleaned_text += " " if cleaned_text else ""
        
        # Append the current instruction
        cleaned_text += instruction

    # Add two newlines at the end
    cleaned_text += "\n\n"
    
    return cleaned_text    

class LidlSpider(scrapy.Spider):
    name = "lidl_spider"
    custom_settings = {
        "DOWNLOAD_DELAY": ".25",
    }

    def start_requests(self):
        json_file_path = 'lidl_recipes.json'
        # Check if the file exists
        if not os.path.exists(json_file_path):
            self.logger.error(f'File not found: {json_file_path}')
            return
        with open(json_file_path, 'r') as file:
            urls = json.load(file)

            for url in urls:
              print(url)
              yield scrapy.Request(url, self.parse)
        
    def parse(self, response):

      title = response.xpath('//h1/text()').get()
      difficulty = response.xpath("(//div[contains(@class, 'mRecipePrepInfo') and contains(@class, 'js_mRecipePrepInfo')]//div[contains(@class, 'mRecipePrepInfo-item')]/@aria-label)[1]").get()
      time = response.xpath("(//div[contains(@class, 'mRecipePrepInfo') and contains(@class, 'js_mRecipePrepInfo')]//div[contains(@class, 'mRecipePrepInfo-item')]/@aria-label)[2]").get()
      nb_servings = response.xpath("//*[@id='oIngredientBox-servingsField']/@data-servings-base").get()

      ingredients = response.xpath("//span[contains(@class, 'oIngredientBox-ingName')][2]/text()").getall()

      ingredients_values = []
      ingredients_units = []
      for span in response.xpath("//td[contains(@class, 'oIngredientBox-ingQuantityCol')]//span[contains(@class, 'oIngredientBox-ingQuantity js_oIngredientBox-ingQuantity js_oIngredientBox-ingFromQuantity')]"):
        value = span.xpath('./text()').get()
        assert str(int(value)) == value, f'Value {value} is not an integer' 
        value = int(value)
        unit = span.xpath('./@data-unit-singular').get()
        
        ingredients_values.append(value)
        ingredients_units.append(unit) #necessary to get a 1-to-1 mapping between values and units
      
      #assert len(ingredients) == len(ingredients_values), f'Number of ingredients ({len(ingredients)}) and number of ingredients values ({len(ingredients_values)}) do not match' 
      
      instruction_list = response.xpath("//div[contains(@class, 'ezrichtext-field')]//li/.//text()").getall()
      instructions = clean_instructions(instruction_list) 
      tip = response.xpath("//p[contains(., 'Conseil')]/text()").get()

      image = response.xpath("//picture/img/@src").getall()[0]
      category = response.xpath("normalize-space(//a[contains(@class, 'mTagBox-linkItem')][1]/text())").get()

      if tip != None:
          instructions += tip

      data = {
          'title': title,
          'category': category,
          'difficulty': difficulty,
          'time': time,
          'servings': nb_servings,
          'ingredients': ingredients,
          'ingredients_values': ingredients_values,
          'ingredients_units': ingredients_units,
          'instructions': instructions,
          'url': response.url,
          'image': image

      }

      yield data


