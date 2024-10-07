import asyncio
from typing import List

import discord
from discord.app_commands import describe
from numpy.distutils.system_info import NotFoundError

from bot import Bot
import commands.ingame_screenshot_commands
import commands.nickname_commands
import commands.event_commands
import commands.setting_commands
import os
import json
import yaml
import logging
import logging.config

from commands.permission_commands import set_permission_roles
from commands.setting_commands import get_redirect_channel_id, get_request_channel_id
from controllers.events_controller import EventAndActivityController
from controllers.nickname_controller import NicknameController
from controllers.panel_controller import PanelController
from data.configuration import CONFIGURATION
from data.models.event import EventType
from exceptions.cancel_exception import CancelException
from exceptions.timeout_exception import TimeoutException
from services.nickname_service import NicknameService
from structures.requesting.request import NicknameRequest, nickname_requests
from ui.embeds.owner_nicknames_profile_embed import BoundingNicknamesEmbed, BoundingNicknameAndActivityEmbed
from ui.embeds.screenshot_embed import RedirectedScreenshotEmbed
from utilities.custom_slash import auto_delete_webhook
from validation.date_validation import validate_date, check_date_range
from validation.permission_validation import user_has_permission

# Блокировщик асинхронных операций, если они заняты
lock = asyncio.Lock()

def setup_logging(config_file='logging.yaml'):
    with open(config_file) as f:
        logger_config = yaml.safe_load(f.read())
        logging.config.dictConfig(logger_config)



setup_logging()
available_guilds = [discord.Object(id=guild_id) for guild_id in CONFIGURATION['DiscordBot']['GUILD_IDS']]
bot = Bot(CONFIGURATION)



async def events_autocomplete(
    interaction: discord.Interaction,
    current: int) -> List[discord.app_commands.Choice[int]]:
    enum_list = (EventType)
    items = {enum_elem.value: enum_elem.name for enum_elem in enum_list}
    return [
        discord.app_commands.Choice(name=event_name, value=event_name)
        for event_name, event_type in sorted(items.items())
        if event_name.lower().startswith(current.lower())
       ][:25]

"""
autocomplete for bound_nickname slash-command allowing a member pull actual nickname's data to discord ui
"""
async def available_nicknames_autocomplete(
    interaction: discord.Interaction,
    current: int) -> List[discord.app_commands.Choice[int]]:
    session = bot.db.get_session_sync()
    service = NicknameService(session)
    nicknames = await service.get_nicknames(interaction.guild.id)
    already_owned_nicknames = await service.get_owned_nicknames(interaction.guild.id, interaction.user.id)
    items_to_delete = [nickname.name for nickname in already_owned_nicknames]
    items = [nickname.name for nickname in nicknames]
    available_nicknames = list(set(items) - set(items_to_delete))
    await session.close()
    return [
        discord.app_commands.Choice(name=nickname, value=nickname)
        for nickname in sorted(available_nicknames)
        if nickname.lower().startswith(current.lower())
       ][:25]

async def all_nicknames_autocomplete(
    interaction: discord.Interaction,
    current: int) -> List[discord.app_commands.Choice[int]]:
    session = bot.db.get_session_sync()
    service = NicknameService(session)
    nicknames = await service.get_all_nicknames(interaction.guild.id)
    items = [nickname.name for nickname in nicknames]
    await session.close()
    return [
        discord.app_commands.Choice(name=nickname, value=nickname)
        for nickname in sorted(items)
        if nickname.lower().startswith(current.lower())
       ][:25]

async def timeout_handler(timeout: int):
    try:
        await asyncio.sleep(timeout)
        if lock.locked():
            print(f"Истек таймер {timeout} секунд. Освобождаем ресурс.")
            lock.release()
    except Exception as e:
        print(f"Ошибка в таймере: {e}")

async def execute_uploading_image(interaction, attachment):
    if lock.locked():
        return await auto_delete_webhook(interaction, f"Данная команда занята, дождитесь, когда её освободят",
                                         CONFIGURATION['SLASH_COMMANDS']['DeleteAfter'],
                                         CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'])
    async with lock:
        session = bot.db.get_session()
        controller = EventAndActivityController()
        event_dict = await controller.generate_event(interaction, session, attachment, bot.config)

        async for session in bot.db.get_session():
            channel_id = await get_redirect_channel_id(session, interaction.guild.id)
            channel = bot.get_channel(channel_id)
            embed = RedirectedScreenshotEmbed(event_dict['events_name'], event_dict['event_ref'],
                                              event_dict['event_time'],
                                              event_dict['event_size'], interaction.user, interaction.user.avatar.url,
                                              event_dict['nicknames_collision'], event_dict['nicknames_manual'])
            await channel.send(embed=embed)
@bot.tree.command(name="скриншот_посещаемости", description="Загрузить скриншот рейда",
                  guilds=available_guilds)
@describe(attachment="Скриншот посещаемости")
async def upload_image_tree(interaction: discord.Interaction, attachment: discord.Attachment):
    try:
        timeout = 300
        await interaction.response.defer(ephemeral=bot.config['SLASH_COMMANDS']['IsResponsesEphemeral'])
        command_task = asyncio.create_task(execute_uploading_image(interaction, attachment))
        handler = asyncio.create_task(timeout_handler(timeout))
        await command_task

        if not handler.done():
            handler.cancel()
    except CancelException as ce:
        pass
    except TimeoutException as te:
        pass


@bot.tree.command(name="настроить_адрессацию", description="Выбрать текстовые каналы и роли доступа",
                  guilds=available_guilds)
@describe(redirect_channel="Текстовой канал для переадрессации", request_channel="Текстовой канал для пользовательских запросов")
async def set_settings(interaction: discord.Interaction, redirect_channel: discord.TextChannel,
                       request_channel: discord.TextChannel)  :
    await interaction.response.defer(ephemeral=CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'])
    session = bot.db.get_session_sync()
    if not await user_has_permission(session, interaction.guild.get_member(interaction.user.id), "setup_accessing"):
        return await auto_delete_webhook(interaction, "У вас нету доступа к данной команде",
                                         CONFIGURATION['SLASH_COMMANDS']['DeleteAfter'],
                                         CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'])

    await commands.setting_commands.set_text_channels(session, interaction.guild.id, redirect_channel.id,
                                                      request_channel.id)
    await session.close()
    await auto_delete_webhook(interaction, f"Каналы для переадрессации скринов рейда установлены "
                                            f"redirect: `{redirect_channel.name}`, request: `{request_channel.name}`",
                                         CONFIGURATION['SLASH_COMMANDS']['DeleteAfter'],
                                         CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'])




@bot.tree.command(name="панель", description="Панель управления бота",
                  guilds=available_guilds)
async def manage_panel(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'])
    session = bot.db.get_session_sync()
    if not await user_has_permission(session, interaction.guild.get_member(interaction.user.id), "view_users_activity"):
        return await auto_delete_webhook(interaction, "У вас нету доступа к данной команде",
                                         CONFIGURATION['SLASH_COMMANDS']['DeleteAfter'],
                                         CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'])

    controller = PanelController(session)
    await controller.launch_panel(interaction)
    #if user_has_permission(interaction.user.roles, "ff"):


@discord.app_commands.autocomplete(nickname=available_nicknames_autocomplete)
@bot.tree.command(name="привязать_ник", description="Отправить запрос на привязку никнейма в Archeage",
                  guilds=available_guilds)
async def bound_nickname(interaction: discord.Interaction, nickname: str):
    await interaction.response.defer()
    guid = interaction.guild.id
    user_id = interaction.user.id
    if (guid, user_id) in nickname_requests:
        return await auto_delete_webhook(interaction, "Ваш запрос уже находится на рассмотрении, "
                                        "дождитесь решения и тогда отправляйте новый",
                                  CONFIGURATION['SLASH_COMMANDS']['DeleteAfter'])




    session = bot.db.get_session_sync()
    request_channel_id = await get_request_channel_id(session, guid)
    channel = bot.get_channel(request_channel_id)
    await session.close()
    await commands.nickname_commands.send_request_on_nickname_bounding(bot.db, interaction, channel, nickname)



@bot.tree.command(name="настройка_доступов", description="Настройка доступов",
                  guilds=available_guilds)
async def edit_roles(interaction: discord.Interaction, admin: discord.Role, moder: discord.Role = None):
    try:
        await interaction.response.defer(ephemeral=CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'])
        session = bot.db.get_session_sync()
        if not await user_has_permission(session, interaction.guild.get_member(interaction.user.id), "setup_accessing"):
            return await auto_delete_webhook(interaction, "У вас нету доступа к данной команде", CONFIGURATION['SLASH_COMMANDS']['DeleteAfter'], CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'])

        admin = admin.id
        if moder:
            moder = moder.id
        await set_permission_roles(session, interaction.guild.id, admin, moder)
        await session.close()
        none_str = "None"
        await auto_delete_webhook(interaction,f"Выбранным ролям выдан доступ: `admin-{admin}`, `moderator-{none_str if moder is None else moder}`", CONFIGURATION['SLASH_COMMANDS']['DeleteAfter'], CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'])
    except Exception as e:
        print(f"Ошибка: {e}")


@discord.app_commands.autocomplete(nickname=all_nicknames_autocomplete)
@bot.tree.command(name="узнать_ник", description="Узнать кому принадлежит никнейм",
                  guilds=available_guilds)
async def check_nickname(interaction: discord.Interaction, nickname: str, date_start: str = None, date_end: str = None):
    await interaction.response.defer(ephemeral=CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'])
    session = bot.db.get_session_sync()
    try:
        is_admin = False
        if await user_has_permission(session, interaction.guild.get_member(interaction.user.id), "view_users_activity"):
            is_admin = True
        member = await commands.nickname_commands.get_member_by_nickname(interaction.guild, session, nickname, is_admin)
        if not member:
            current = nickname
            previous = []
        else:
            current, previous = await commands.nickname_commands.get_nicknames_by_member(session, member)

        if is_admin:
            panel = PanelController(session)
            dates = date_start, date_end
            if date_end is None or date_start is None:
                dates = None
                is_dates_valid = False
            else:
                is_dates_valid = check_date_range(date_start, date_end)

            if not is_dates_valid:
                return await auto_delete_webhook(interaction,
                                                 "Введите даты в правильном формате: `DD-MM-YYYY` и выполните условие start_date < end_date",
                                                 CONFIGURATION['SLASH_COMMANDS']['DeleteAfter'],
                                                 CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'])

            activity, salary = panel.get_member_activities_and_salary(interaction, nickname, dates)
            embed = BoundingNicknameAndActivityEmbed(None, current, previous, activity, salary)
            return await interaction.followup.send(embed=embed, ephemeral=CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'])
        else:
            embed = BoundingNicknamesEmbed(member, current, previous)
            return await interaction.followup.send(embed=embed, ephemeral=CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'])
    except NotFoundError as e:
        return await auto_delete_webhook(interaction,
                                   f"{nickname} не было привязано. Чтобы привязать никнейм используйте `/привязать_ник`",
                                   CONFIGURATION['SLASH_COMMANDS']['DeleteAfter'],
                                   CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'])

    finally:
        await session.close()

@bot.tree.context_menu(name="профиль",
                  guilds=available_guilds)
async def profile_nickname(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.defer(ephemeral=CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'])
    session = bot.db.get_session_sync()
    try:
        current, previous = await commands.nickname_commands.get_nicknames_by_member(session, member)
        embed = BoundingNicknamesEmbed(member, current, previous)
        return await interaction.followup.send(embed=embed, ephemeral=CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'])
    except NotFoundError as e:
        return await auto_delete_webhook(interaction,
                                   f"{member.name} не было привязано. Чтобы привязать никнейм используйте `/привязать_ник`",
                                   CONFIGURATION['SLASH_COMMANDS']['DeleteAfter'],
                                   CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'])

    finally:
        await session.close()







bot.startup()

token = CONFIGURATION['DiscordBot']['TOKEN']
bot.run(token)





