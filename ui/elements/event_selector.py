import discord.ui
from discord import SelectOption

from data.models.event import EventType

# Элемент управления для выбора ивентов из списка доступных
class EventSelector(discord.ui.Select):
    def __init__(self):
        self.events = [SelectOption(label=etype.value, value=etype.value) for etype in EventType]
        # discord has limit options to show
        self.events = self.events[:25] if len(self.events) > 25 else self.events
        max_select_count = 4
        placeholder_text = "Выберите ивенты..."
        super().__init__(placeholder=placeholder_text, max_values=max_select_count, options=self.events)