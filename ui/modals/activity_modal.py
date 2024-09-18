from datetime import datetime

import discord
from discord import TextStyle

from data.models.event import EventType
from ui.modals.base_modal import BaseModal

from discord.ui import TextInput
from enum import EnumMeta

from validation.date_validation import check_date_range


class DateInputModal(BaseModal):
    def __init__(self):
        super().__init__("Укажите диапазон дат")
        self.add_item(TextInput(label="Начальная дата (YYYY-MM-DD)", placeholder="2024-05-24", style=TextStyle.short))
        self.add_item(TextInput(label="Конечная дата (YYYY-MM-DD)", placeholder="2024-05-25", style=TextStyle.short))

        self.start = None
        self.end = None
        self.on_submit = self.callback

    async def callback(self, interaction: discord.Interaction):
        start_date = self.children[0].value
        end_date = self.children[1].value

        date_format: str = "%Y-%m-%d"
        if not check_date_range(start_date, end_date, date_format):
            await interaction.response.send_message("Введите время в правильном формате и в правильном диапазоне start_date < end_date")
            return
        self.start = datetime.strptime(start_date, date_format)
        self.end = datetime.strptime(end_date, date_format)
        self.stop()
        await interaction.response.defer()



