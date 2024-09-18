import json

import discord
from async_timeout import timeout
from discord.ui import View

from exceptions.timeout_exception import TimeoutException
from ui.elements.merge_selector import MergeDropdown
from ui.views.base_view import BaseView, CancelledView


class MergedResolverView(CancelledView):
    def __init__(self, merged_names, merged_names_len, choices: [], main_view=None, message = None):
        super().__init__()
        self.is_timeout = False
        if main_view is None:
            self.main_view = self
        else:
            self.main_view = main_view
        self.message = message
        self.choices = choices
        not_selected = list(set(merged_names[0][0]) - set(self.choices))
        self.add_item(MergeDropdown(not_selected, self.update_embed))
        self.names_len = merged_names_len
        cropped_image = merged_names[0][1]
        self.file = cropped_image
        self.merged_names = merged_names[1:]
        self.embed = discord.Embed(title=f"Конфликт {self.names_len-len(self.merged_names)}/{self.names_len}",
                                   description=f"Бот не смог разобрать, кто из этих участников был в рейде, выберите правильного участника рейда из списка.",
                                   ).set_image(url=f"attachment://{cropped_image.filename}")

    async def on_timeout(self) -> None:
        self.is_timeout = True
        self.stop()

    async def update_embed(self, interaction: discord.Interaction, choice):
        self.choices.append(choice)
        if len(self.merged_names) > 0:
            view = MergedResolverView(self.merged_names, self.names_len, self.choices, self.main_view, message=self.message)
            await interaction.response.edit_message(embed=view.embed, view=view, attachments=[view.file])
            return
        else:
            self.main_view.stop()
