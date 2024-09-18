import discord
from discord.ext import commands
from discord.ui import Select

class MergeDropdown(Select):
    def __init__(self, merged_names, on_select):
        options = [discord.SelectOption(label=name) for name in merged_names]
        super().__init__(placeholder="Выбрать участника рейда", min_values=1, max_values=1, options=options)
        self.on_select = on_select

    async def callback(self, interaction: discord.Interaction):
        await self.on_select(interaction, self.values[0])