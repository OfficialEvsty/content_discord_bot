import json
import logging
from datetime import datetime, date
from typing import List, Dict

import discord
from commands.calculating.activity_commands import collect_activities_by_nickname, calculate_activity
from commands.calculating.salary_commands import calculate_salary_by_nickname
from data.configuration import CONFIGURATION
from data.models.event import EventType
from data.models.nickname import Nickname
from services.event_service import EventService
from services.nickname_service import NicknameService
from ui.embeds.manage_embed import ManagerEmbed
from ui.embeds.owner_nicknames_profile_embed import BoundingNicknameAndActivityEmbed
from ui.views.manage_panel_view import ManagerPanelView
from ui.views.user_statistics_view import UserStatisticsView

logger = logging.getLogger("app.controllers")

class PanelController:
    def __init__(self, session):
        self.session = session
    async def launch_panel(self, interaction: discord.Interaction):
        panel_view = ManagerPanelView(self)
        panel_embed = ManagerEmbed(interaction.user, ">>> *Панель - лучший инструмент для просмотра статистики активностей и зарплат мемберов*", is_formatted=True)
        panel_msg = await interaction.followup.send(view=panel_view, embed=panel_embed, file=panel_embed.file)
        panel_view.message = panel_msg

    async def get_nickname_activities(self, interaction: discord.Interaction, date1 = None, date2 = None, nicknames_str: [str] = None):
        if nicknames_str is None:
            nicknames_str = []
        guid = interaction.guild.id
        nickname_service = NicknameService(self.session)
        nicknames = []
        if len(nicknames_str) > 0:
            for nickname in nicknames_str:
                nicknames.extend(await nickname_service.get_nicknames(guid, nickname))
        else:
            nicknames = await nickname_service.get_nicknames(guid)
        event_service = EventService(self.session)
        ids = [nickname.id for nickname in nicknames]
        activities = await event_service.get_activities(guid, date1, date2, ids)

        activity_dict = await collect_activities_by_nickname(activities)
        return activity_dict


    async def get_member_activities_and_salary(self, interaction: discord.Interaction, member: discord.Member, nickname: Nickname, previous: [str]):
        # if not dates:
        #     temp = datetime.now()
        #     start_month_date = datetime(temp.year, temp.month, 1)
        #     days_count_in_current_month = (date(start_month_date.year, start_month_date.month+1, 1) - start_month_date.date()).days
        #     end_month_date = datetime(temp.year, temp.month, days_count_in_current_month)
        #     dates = (start_month_date, end_month_date)
        # else:
        #     date_format: str = "%d-%m-%Y"
        #     dates = datetime.strptime(dates[0], date_format), datetime.strptime(dates[1], date_format)

        activity_dict = await self.get_nickname_activities(interaction)
        view = UserStatisticsView(member, nickname, previous, activity_dict)
        message = await interaction.followup.send(view=view, ephemeral=CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'])
        view.message = message
        await view.update_ui(interaction)





