import discord
from discord import ButtonStyle

from data.configuration import CONFIGURATION
from ui.views.base_view import BaseView
from utilities.custom_slash import auto_delete_webhook


class ConfirmView(BaseView):
    def __init__(self, accept_callback, reject_callback, owner):
        super().__init__()
        self.view_owner = owner
        self.button_accept = discord.ui.Button(label="Да", style=ButtonStyle.success)
        self.button_reject = discord.ui.Button(label="Нет", style=ButtonStyle.danger)

        self.accept_callback = accept_callback
        self.reject_callback = reject_callback

        self.button_accept.callback = self.accept
        self.button_reject.callback = self.reject
        self.add_item(self.button_accept)
        self.add_item(self.button_reject)

    async def accept(self, interaction):
        if not interaction.user == self.view_owner:
            return await auto_delete_webhook(interaction, "Вы не можете взаимодействовать с этим сообщением, так как не вы его владелец",
                                      CONFIGURATION['SLASH_COMMANDS']['DeleteAfter'],
                                      CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'])
        await self.accept_callback(interaction)
        self.stop()
    async def reject(self, interaction):
        if not interaction.user == self.view_owner:
            return await auto_delete_webhook(interaction, "Вы не можете взаимодействовать с этим сообщением, так как не вы его владелец",
                                      CONFIGURATION['SLASH_COMMANDS']['DeleteAfter'],
                                      CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'])
        await self.reject_callback(interaction)
        self.stop()
