import json
import logging


import discord

from sqlalchemy.ext.asyncio import AsyncSession
from services.nickname_service import NicknameService
from structures.requesting.request import nickname_requests
from ui.views.simple_response_view import ConfirmView

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






