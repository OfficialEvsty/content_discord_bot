import json

import discord
from discord import app_commands
import schedule
from discord.ext import tasks
import commands.nickname_commands
import logging

from data.configuration import CONFIGURATION
from data.database import Database

class Bot(discord.Client):
    def __init__(self, config):
        intents = discord.Intents.all()
        super().__init__(intents=intents)
        self.synced = False
        self.tree = app_commands.CommandTree(self)
        self.config = config
        self.db = None


    @tasks.loop(seconds=3600)
    async def pull_nicknames_task(self):
        await self.wait_until_ready()  # Ждем, пока бот полностью запустится
        if not self.is_closed():
            try:
                guids = self.config["DiscordBot"]["GUILD_IDS"]
                for guid in guids:
                    await commands.nickname_commands.add_nicknames(guid, self.db.get_session(), self.config['ArcheAge'])
            except Exception as e:
                logging.root.error(f"Ошибка во время выполнения таймер-команды запроса к серверу: {e}")
            logging.root.info("Тайм-команда успешно отработала")

    def startup(self):
        @self.event
        async def on_ready():

            # Инициализируем базу данных
            self.db = Database(self.config["Database"])
            # Асинхронно вызываем метод для инициализации базы данных
            self.db.init_db()
            await self.wait_until_ready()
            if not self.synced:
                guilds = self.config['DiscordBot']['GUILD_IDS']
                if len(guilds) == 0:
                    await self.tree.sync()
                for guild_id in guilds:
                    guild = discord.Object(id=guild_id)
                    await self.tree.sync(guild=guild)
                    print(f"Синхронизация команд завершена для сервера {guild_id}")
                self.synced = True

            if not self.pull_nicknames_task.is_running():  # Проверяем, что задача не запущена
                self.pull_nicknames_task.start()

            print("We have logged in as {0.user}".format(self))
