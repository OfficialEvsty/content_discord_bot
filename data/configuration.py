import json

CONFIGURATION = None
with open("config.json") as file:
    CONFIGURATION = json.load(file)
