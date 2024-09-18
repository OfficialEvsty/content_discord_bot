from typing import List, Dict

import discord
from commands.calculating.activity_commands import collect_activities_by_nickname
from services.event_service import EventService
from services.nickname_service import NicknameService
from ui.embeds.manage_embed import ManagerEmbed
from ui.views.manage_panel_view import ManagerPanelView


class PanelController:
    def __init__(self, session):
        self.session = session
    async def launch_panel(self, interaction: discord.Interaction):
        panel_view = ManagerPanelView(self)
        panel_embed = ManagerEmbed(interaction.user, ">>> *Панель - лучший инструмент для просмотра статистики активностей и зарплат мемберов*", is_formatted=True)
        panel_msg = await interaction.followup.send(view=panel_view, embed=panel_embed, file=panel_embed.file)
        panel_view.message = panel_msg

    async def get_nickname_activities(self, interaction: discord.Interaction, date1, date2):
        guid = interaction.guild.id
        nickname_service = NicknameService(self.session)
        nicknames = await nickname_service.get_nicknames(guid)
        event_service = EventService(self.session)
        ids = [nickname.id for nickname in nicknames]
        activities = await event_service.get_activities(guid, date1, date2, ids)

        activity_dict = await collect_activities_by_nickname(self.session, activities)
        return activity_dict



