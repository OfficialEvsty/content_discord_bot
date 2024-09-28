import json

EMOJIS = {}
with open("utilities/custom/emojis.json") as file:
    EMOJIS = json.load(file)
