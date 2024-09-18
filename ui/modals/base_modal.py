import json

import discord.ui

with open("config.json") as file:
    config = json.load(file)

class BaseModal(discord.ui.Modal):
    def __init__(self, title):
        super().__init__(title=title, timeout=config['SLASH_COMMANDS']['Timeout'])