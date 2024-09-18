import json
from typing import Optional

import discord.ui
from discord import SelectOption

from ui.embeds.nicknames_table import NicknameTableEmbed
import logging

from ui.views.base_view import BaseView, CancelledView

logger = logging.getLogger("app.ui")


class ManualConfirmMessageView(CancelledView):
    def __init__(self, available_names: [], choices: [], main_view = None, message = None):
        super().__init__()
        if main_view is None:
            self.main_view = self
        else:
            self.main_view = main_view
        self.is_done = False
        self.message = message
        self.choices = choices
        self.available_names = available_names
        accept_button = discord.ui.Button(label="Указать вручную")
        reject_button = discord.ui.Button(label="Все правильно")
        self.embed = discord.Embed(title="Если кто-то не был распознан, то его можно указать вручную из списка :mag:")
        if len(choices) > 0:
            self.embed.description = f"```Были дополнительно выбраны ники ({len(choices)}): \n"+"\n".join(choices)+"```"
        accept_button.callback = self.accept_button_callback
        reject_button.callback = self.reject_button_callback
        self.add_item(accept_button)
        self.add_item(reject_button)

    async def on_timeout(self):
        self.is_timeout = True


    async def accept_button_callback(self, interaction: discord.Interaction):
        try:
            view = PagedSelectorView(self.available_names, self.choices, self.main_view, self.message)
            return await interaction.response.edit_message(embed=self.embed, view=view)
        except Exception as e:
            logger.error(f"Ошибка при обработке события {self.accept_button_callback} на форме {self}: {e}")

    async  def reject_button_callback(self, interaction: discord.Interaction):
        try:
            self.is_done = True
            self.main_view.stop()
            logger.info(f"Участник {interaction.user.name}:{interaction.user.id} заполнил форму {self}")
        except Exception as e:
            logger.error(f"Ошибка при обработке события {self.reject_button_callback} на форме {self}: {e}")




class PagedSelectorView(CancelledView):
    def __init__(self, available_names, choices, confirm_view, message):
        super().__init__()
        sorted_names = sorted(available_names, key=lambda name: (name[0].isalpha(), name))
        self.message = message
        self.confirm_view = confirm_view
        self.available_names = available_names
        self.choices = choices
        self.current_page = 0
        self.page_size = 25
        self.options = [discord.SelectOption(label=f"{sorted_names[i]}") for i in range(0, len(sorted_names))]
        self.confirm_button = discord.ui.Button(label="Подтвердить", style=discord.ButtonStyle.success)
        self.cancel_button = discord.ui.Button(label="Отменить", style=discord.ButtonStyle.danger)
        self.update_selector()


    def update_selector(self):
        # Создаем селектор с 25 опциями на текущей странице
        start_index = self.current_page * self.page_size
        end_index = start_index + self.page_size
        options_page = self.options[start_index:end_index]
        self.select = discord.ui.Select(placeholder=f"Выберите никнемы {start_index + 1}-{end_index}",
                                   options=options_page, max_values=min(len(self.options) - start_index, 10))
        self.select.callback = self.select_callback
        # Очищаем старые селекторы и добавляем новый
        self.clear_items()
        self.add_item(self.select)

        if start_index > 24:
            prev_button = discord.ui.Button(label="Предыдущая страница", style=discord.ButtonStyle.primary)
            prev_button.callback = self.prev_page
            self.add_item(prev_button)

        self.confirm_button.callback = self.on_confirm
        self.cancel_button.callback = self.on_cancel
        self.add_item(self.confirm_button)
        self.add_item(self.cancel_button)

        # Добавляем кнопку "Следующая страница", если есть еще варианты
        if end_index < len(self.options):
            next_button = discord.ui.Button(label="Следующая страница", style=discord.ButtonStyle.primary)
            next_button.callback = self.next_page
            self.add_item(next_button)

    async def on_confirm(self, interaction: discord.Interaction):
        new_available = list(set(self.choices) ^ set(self.available_names))
        print(self.choices)
        print(self.confirm_view.choices)
        view = ManualConfirmMessageView(new_available, self.choices, self.confirm_view, self.message)
        await interaction.response.edit_message(view=view, embed=view.embed)

    async def on_cancel(self, interaction: discord.Interaction):
        self.choices.clear()
        self.confirm_view.choices.clear()
        view = ManualConfirmMessageView(self.available_names, self.choices, self.confirm_view, self.message)
        await interaction.response.edit_message(view=view, embed=view.embed)

    async def select_callback(self, interaction: discord.Interaction):
        self.choices.extend((set(self.select.values) - set(self.choices)))
        await interaction.response.edit_message(embed=NicknameTableEmbed(self.choices))

    async def next_page(self, interaction: discord.Interaction):
        self.current_page += 1
        self.update_selector()
        await interaction.response.edit_message(view=self)

    async def prev_page(self, interaction: discord.Interaction):
        self.current_page -= 1
        self.update_selector()
        await interaction.response.edit_message(view=self)