import json
from typing import List

import discord
from numpy.distutils.system_info import NotFoundError
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

async def get_member_by_nickname(guild: discord.Guild, session: AsyncSession, nickname: str) -> discord.Member:
    nickname_service = NicknameService(session)
    owner_id = await nickname_service.get_member_id_by_nickname(guild.id, nickname)
    if owner_id:
        return guild.get_member(owner_id)
    raise NotFoundError

async def get_nicknames_by_member(session: AsyncSession, member: discord.Member) -> (str, List[str]):
    previous: List[str] = []
    current: str = ""

    service = NicknameService(session)
    owned = await service.get_owned_nicknames(member.guild.id, member.id)
    if len(owned) == 0:
        raise NotFoundError()
    for nickname in owned:
        await session.refresh(nickname, ['archived_nickname'])
        if nickname.is_archived:
            previous.append(f"{nickname.name}:<15 {nickname.archived_nickname.archived_at.strftime('%d %B, %Y')}")
            continue
        current = f"{nickname.name}:<15 {nickname.archived_nickname.archived_at.strftime('%d %B, %Y')}"
    return current, previous




