import json
import logging
from code import interact

import discord
from numpy.distutils.system_info import NotFoundError
from requests import session
from sqlalchemy.ext.asyncio import AsyncSession

from commands.nickname_commands import get_member_by_nickname, get_nicknames_by_member
from data.configuration import CONFIGURATION
from services.nickname_service import NicknameService
from structures.requesting.request import nickname_requests, NicknameRequest
from ui.embeds.owner_nicknames_profile_embed import BoundingNicknamesEmbed
from ui.views.simple_response_view import ConfirmView
from utilities.custom_slash import auto_delete_webhook

logger = logging.getLogger("app.controllers")

class NicknameController:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def bound_nickname_to_member(self, interaction: discord.Interaction, user_id, nickname: str):
        try:
            popped_request = nickname_requests.pop((interaction.guild.id, user_id))
            nickname_service = NicknameService(self.session)
            result = await nickname_service.get_nicknames(interaction.guild.id, nickname)
            if result:
                nick = result[0]
                if nick.is_borrowed:
                    answer: bool
                    async def accept(interaction: discord.Interaction):
                        nonlocal answer
                        answer = True
                        await interaction.response.defer()

                    async def reject(interaction: discord.Interaction):
                        nonlocal answer
                        answer = False
                        await interaction.response.defer()

                    view = ConfirmView(accept, reject, interaction.user)
                    msg = await interaction.followup.send("Данный ник занят, хотите продолжить?", view=view)
                    await view.wait()
                    await msg.delete()
                    if answer:
                        await nickname_service.bound_nickname(guid=interaction.guild.id, user_id=user_id, nickname=nick)
                    else:
                        pass
                else:
                    await nickname_service.bound_nickname(guid=interaction.guild.id, user_id=user_id, nickname=nick)
                    #await interaction.followup.edit_message(message_id=message_id, view=None)
            else:
                logger.warning(f"В базе данных нет никнейма: {nickname}")
                #await interaction.followup.edit_message(message_id=message_id, view=None)
        except Exception as e:
            logger.error(f"Ошибка в {self}: {e}")
            return
        finally:
            await self.session.close()

    async def get_owned_nicknames(self, interaction: discord.Interaction, user_id):
        service = NicknameService(self.session)
        owned = []
        owned = await service.get_owned_nicknames(interaction.guild.id, user_id)

    async def get_nickname_profile(self, member:discord.Member, interaction: discord.Interaction):

        current, previous = await get_nicknames_by_member(self.session, member)
        embed = BoundingNicknamesEmbed(interaction.user, member, current, previous)
        return await interaction.followup.send(embed=embed)





