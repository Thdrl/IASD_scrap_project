import requests
import json
import psycopg2


conn = psycopg2.connect(
    dbname="your_dbname", 
    user="your_username", 
    password="your_password", 
    host="localhost"
)
cursor = conn.cursor()

# The database will consist of a single table with the following columns:
# 