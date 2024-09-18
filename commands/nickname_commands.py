import json

import discord
from sqlalchemy.ext.asyncio import AsyncSession

from services.nickname_service import NicknameService
from structures.requesting.request import nickname_requests, NicknameRequest
from ui.embeds.switch_nickname_request_embed import SwitchNicknameEmbed
from ui.views.switch_nickname_request_view import SwitchNicknameView
from utilities.custom_slash import auto_delete_webhook
from web.nickname_parsing import get_nicknames_from_archeage_website

with open('config.json') as file:
    config = json.load(file)

async def add_nicknames(guid, session_generator, config):
    async for session in session_generator:
        service = NicknameService(session)
        result = await service.get_nicknames(guid)
        existing_nicknames = [] if result is None else [nickname.name for nickname in result]
        parsed_nicknames = await get_nicknames_from_archeage_website(config)
        new_nicknames = set(parsed_nicknames) - set(existing_nicknames)
        to_list = list(new_nicknames)
        await service.add_or_update_nicknames(guid, nicknames=to_list, )


async def create_nickname_request(interaction: discord.Interaction, session: AsyncSession, nickname: str):
    user = interaction.user

async def send_request_on_nickname_bounding(database, interaction: discord.Interaction,
                                            channel: discord.TextChannel, nickname: str):
    view = SwitchNicknameView(database=database, user=interaction.user, nickname=nickname)
    embed = SwitchNicknameEmbed(user=interaction.user, nickname=nickname)
    msg = await channel.send(view=view, embed=embed)
    view.message = msg
    key = (interaction.guild.id, interaction.user.id)
    nickname_requests.setdefault(key, None)
    nickname_requests[key] = NicknameRequest(msg, nickname)

    await auto_delete_webhook(interaction, "Ваш запрос был отправлен в специальный канал для подтверждения, "
                                    "если его подтвердят, то вам придет уведомление в лс",
                              config['SLASH_COMMANDS']['DeleteAfter'])


