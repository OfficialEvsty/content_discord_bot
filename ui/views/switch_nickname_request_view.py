import discord
from PIL.ImageEnhance import Color
from aiohttp.log import access_logger
from discord import ButtonStyle
from discord.ui import Button
from sqlalchemy.ext.asyncio import AsyncSession
from controllers.nickname_controller import NicknameController
from data.configuration import CONFIGURATION
from structures.requesting.request import nickname_requests
from ui.embeds.switch_nickname_request_embed import SwitchNicknameEmbed
from ui.views.base_view import BaseView

import logging

from utilities.custom_slash import auto_delete_webhook
from validation.permission_validation import user_has_permission

logger = logging.getLogger("app.ui")

class SwitchNicknameView(BaseView):
    def __init__(self, database, user: discord.User, nickname: str, msg = None):
        super().__init__()
        self.database = database
        self.user = user
        self.nickname = nickname
        self.message: discord.Message = msg
        self.accept_button = Button(label="Подтвердить", style=ButtonStyle.success)
        self.reject_button = Button(label="Отклонить", style=ButtonStyle.danger)
        self.accept_button.callback = self.accept_callback
        self.reject_button.callback = self.reject_callback
        self.add_item(self.accept_button)
        self.add_item(self.reject_button)

    async def on_timeout(self) -> None:
        if self.message:
            updated_view = SwitchNicknameView(self.database, self.user, self.nickname, self.message)
            await self.message.edit(view=updated_view)
        else:
            logger.info(f"View: {self} не смогло обновиться, так как сообщения к которому оно прикреплено не существует")

    async def accept_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if not user_has_permission(interaction.guild.get_member(interaction.user.id), "nicknames_control"):
            return await auto_delete_webhook(interaction, "У вас нет доступа для этого действия",
                                      CONFIGURATION['SLASH_COMMANDS']['DeleteAfter'],
                                      CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'])
        session = self.database.get_session_sync()
        try:

            controller = NicknameController(session)
            await controller.bound_nickname_to_member(interaction, self.user.id, self.nickname)
            colored_embed = SwitchNicknameEmbed(self.user, self.nickname, discord.Color.green())
            await self.message.edit(embed=colored_embed, view=None)
            await self.user.send(embed=discord.Embed(title=f"Ваш запрос на присваивание никнейма `{self.nickname}` принят 🎉",
                                                     color=discord.Color.green()))
        except Exception as e:
            logger.error(f"Ошибка при обработке события {self.accept_callback}: {e}")
        finally:
            await session.close()
    async def reject_callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            if not user_has_permission(interaction.guild.get_member(interaction.user.id), "nicknames_control"):
                return await auto_delete_webhook(interaction, "У вас нет доступа для этого действия",
                                          CONFIGURATION['SLASH_COMMANDS']['DeleteAfter'],
                                          CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'])
            colored_embed = SwitchNicknameEmbed(self.user, self.nickname, discord.Color.red())
            nickname_requests.pop((interaction.guild.id, self.user.id))
            await self.message.edit(embed=colored_embed, view=None)
            await self.user.send(embed=discord.Embed(title=f"Ваш запрос на присваивание никнейма `{self.nickname}` отклонен 🥺",
                                                     color=discord.Color.red()))
        except Exception as e:
            logger.error(f"Ошибка при обработке события {self.reject_callback}: {e}")