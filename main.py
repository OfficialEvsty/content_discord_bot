
from typing import List
import logging
import discord
from discord.app_commands import describe

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
from commands.setting_commands import get_redirect_channel_id, get_request_channel_id
from controllers.events_controller import EventAndActivityController
from controllers.panel_controller import PanelController
from data.configuration import CONFIGURATION
from data.models.event import EventType
from exceptions.cancel_exception import CancelException
from services.nickname_service import NicknameService
from structures.requesting.request import NicknameRequest, nickname_requests
from ui.embeds.screenshot_embed import RedirectedScreenshotEmbed
from utilities.custom_slash import auto_delete_webhook
from validation.permission_validation import user_has_permission


def setup_logging(config_file='logging.yaml'):
    with open(config_file) as f:
        logger_config = yaml.safe_load(f.read())
        logging.config.dictConfig(logger_config)



setup_logging()
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


@discord.app_commands.autocomplete(event_type=events_autocomplete)
@bot.tree.command(name="скриншот_посещаемости", description="Загрузить скриншот рейда",
                  guild=discord.Object(id=bot.config["DiscordBot"]["GUILD_ID"]))
@describe(attachment="Скриншот посещаемости")
async def upload_image_tree(interaction: discord.Interaction, attachment: discord.Attachment,
                            event_type: str):
    try:
        await interaction.response.defer(ephemeral=bot.config['SLASH_COMMANDS']['IsResponsesEphemeral'])
        session = bot.db.get_session()
        controller = EventAndActivityController()
        event_dict = await controller.generate_event(interaction, session, attachment, bot.config, event_type)

        async for session in bot.db.get_session():
            channel_id = await get_redirect_channel_id(session, interaction.guild.id)
            channel = bot.get_channel(channel_id)
            embed = RedirectedScreenshotEmbed(event_dict['event_name'], event_dict['event_ref'], event_dict['event_time'],
                                              event_dict['event_size'], interaction.user, interaction.user.avatar.url,
                                              event_dict['nicknames_collision'], event_dict['nicknames_manual'])
            await channel.send(embed=embed)
    except CancelException as ce:
        pass
    except TimeoutError as te:
        pass


@bot.tree.command(name="настроить_адрессацию", description="Выбрать текстовые каналы и роли доступа",
                  guild=discord.Object(id=bot.config["DiscordBot"]["GUILD_ID"]))
@describe(redirect_channel="Текстовой канал для переадрессации", request_channel="Текстовой канал для пользовательских запросов")
async def set_settings(interaction: discord.Interaction, redirect_channel: discord.TextChannel,
                       request_channel: discord.TextChannel)  :
    await interaction.response.defer(ephemeral=CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'])
    if not user_has_permission(interaction.guild.get_member(interaction.user.id), "setup_accessing"):
        return await auto_delete_webhook(interaction, "У вас нету доступа к данной команде",
                                         CONFIGURATION['SLASH_COMMANDS']['DeleteAfter'],
                                         CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'])
    session = bot.db.get_session_sync()
    await commands.setting_commands.set_text_channels(session, interaction.guild.id, redirect_channel.id,
                                                      request_channel.id)
    await session.close()
    await auto_delete_webhook(interaction, f"Каналы для переадрессации скринов рейда установлены "
                                            f"redirect: `{redirect_channel.name}`, request: `{request_channel.name}`",
                                         CONFIGURATION['SLASH_COMMANDS']['DeleteAfter'],
                                         CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'])




@bot.tree.command(name="панель", description="Панель управления бота",
                  guild=discord.Object(id=bot.config["DiscordBot"]["GUILD_ID"]))
async def manage_panel(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'])
    if not user_has_permission(interaction.guild.get_member(interaction.user.id), "view_users_activity"):
        return await auto_delete_webhook(interaction, "У вас нету доступа к данной команде",
                                         CONFIGURATION['SLASH_COMMANDS']['DeleteAfter'],
                                         CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'])
    session = bot.db.get_session_sync()
    controller = PanelController(session)
    await controller.launch_panel(interaction)
    #if user_has_permission(interaction.user.roles, "ff"):


@discord.app_commands.autocomplete(nickname=available_nicknames_autocomplete)
@bot.tree.command(name="привязать_ник", description="Отправить запрос на привязку никнейма в Archeage",
                  guild=discord.Object(id=bot.config["DiscordBot"]["GUILD_ID"]))
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
                  guild=discord.Object(id=bot.config["DiscordBot"]["GUILD_ID"]))
async def edit_roles(interaction: discord.Interaction, admin: discord.Role, moder: discord.Role = None):
    await interaction.response.defer(ephemeral=CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'])
    if not user_has_permission(interaction.guild.get_member(interaction.user.id), "setup_accessing"):
        return await auto_delete_webhook(interaction, "У вас нету доступа к данной команде", CONFIGURATION['SLASH_COMMANDS']['DeleteAfter'], CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'])
    with open("roles_permissions.json", "r") as file:
        data = json.load(file)
        data['roles']['admin'] = admin.id
        if moder:
            data['roles']['moderator'] = moder.id
    with open("roles_permissions.json", "w") as file:
        json.dump(data, file)
    none_str = "None"
    await auto_delete_webhook(interaction,f"Выбранным ролям выдан доступ: `admin-{admin}`, `moderator-{none_str if moder is None else moder}`", CONFIGURATION['SLASH_COMMANDS']['DeleteAfter'], CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'])






bot.startup()


bot.run(os.getenv('TOKEN'))





