import logging

import discord
from discord.ui import Button

from ui.elements.event_selector import EventSelector
from ui.views.base_view import CancelledView

logger = logging.getLogger("app.ui")

class EventSelectorView(CancelledView):
    def __init__(self, events: []):
        super().__init__()
        self.events = events
        self.selector = EventSelector()
        self.add_item(self.selector)
        self.accept_button = Button(label="Подтвердить", style=discord.ButtonStyle.green)
        self.accept_button.callback = self.accept_callback

    async def accept_callback(self, interaction: discord.Interaction):
        user = interaction.user
        guild = interaction.guild
        self.events = self.selector.values
        self.stop()
        logger.info(f"Пользователь: {user.name} выбрал активности {self.events} на сервере {guild.name}")