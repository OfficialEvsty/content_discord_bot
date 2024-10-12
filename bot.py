import json
from typing import List

import discord
from discord import app_commands
import schedule
from discord.app_commands import AppCommand
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
            # for guild_id in self.config['DiscordBot']['GUILD_IDS']:
            #     guild = discord.Object(id=guild_id)
            #
            #     # Получаем все команды, зарегистрированные для этой гильдии
            #     guild_commands = await self.tree.fetch_commands(guild=guild)
            #
            #     # Проходим по каждой команде и удаляем её
            #     for command in guild_commands:
            #         self.tree.remove_command(command.name, guild=guild)
            #         print(f"Удалена команда: {command.name} в гильдии {guild_id}")
            #
            # print(f"Все команды для гильдии {guild_id} удалены")
            #
            # global_commands: List[AppCommand] = await self.tree.fetch_commands()
            #
            # for command in global_commands:
            #     # Удаляем каждую команду
            #     await command.delete()
            # print(f"Удалены все глобальные команды")
            # Инициализируем базу данных
            self.db = Database(self.config["Database"])
            # Асинхронно вызываем метод для инициализации базы данных
            self.db.init_db()
            await self.wait_until_ready()
            if not self.synced:
                guilds = self.config['DiscordBot']['GUILD_IDS']
                if self.config['DiscordBot']['IS_GLOBAL_SYNC']:
                    await self.tree.sync()
                else:
                    for guild_id in guilds:
                        guild = discord.Object(id=guild_id)
                        await self.tree.sync(guild=guild)
                        print(f"Синхронизация команд завершена для сервера {guild_id}")
                self.synced = True

            if not self.pull_nicknames_task.is_running():  # Проверяем, что задача не запущена
                self.pull_nicknames_task.start()

            print("We have logged in as {0.user}".format(self))
