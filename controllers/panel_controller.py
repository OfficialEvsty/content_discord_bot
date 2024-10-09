import json
import logging
from datetime import datetime, date
from typing import List, Dict

import discord
from commands.calculating.activity_commands import collect_activities_by_nickname, calculate_activity
from commands.calculating.salary_commands import calculate_salary_by_nickname
from data.models.event import EventType
from services.event_service import EventService
from services.nickname_service import NicknameService
from ui.embeds.manage_embed import ManagerEmbed
from ui.views.manage_panel_view import ManagerPanelView

logger = logging.getLogger("app.controllers")

class PanelController:
    def __init__(self, session):
        self.session = session
    async def launch_panel(self, interaction: discord.Interaction):
        panel_view = ManagerPanelView(self)
        panel_embed = ManagerEmbed(interaction.user, ">>> *Панель - лучший инструмент для просмотра статистики активностей и зарплат мемберов*", is_formatted=True)
        panel_msg = await interaction.followup.send(view=panel_view, embed=panel_embed, file=panel_embed.file)
        panel_view.message = panel_msg

    async def get_nickname_activities(self, interaction: discord.Interaction, date1, date2, nicknames_str: [str] = None):
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


    async def get_member_activities_and_salary(self, interaction: discord.Interaction, nickname: str, dates: tuple = None):
        if not dates:
            temp = datetime.now()
            start_month_date = datetime(temp.year, temp.month, 1)
            days_count_in_current_month = (date(start_month_date.year, start_month_date.month+1, 1) - start_month_date.date()).days
            end_month_date = datetime(temp.year, temp.month, days_count_in_current_month)
            dates = (start_month_date, end_month_date)
        else:
            date_format: str = "%d-%m-%Y"
            dates = datetime.strptime(dates[0], date_format), datetime.strptime(dates[1], date_format)

        activity_dict = await self.get_nickname_activities(interaction,
                                                           date1=dates[0],
                                                           date2=dates[1],
                                                           nicknames_str=[nickname])
        try:
            with open('commands/calculating/parameters.json') as file:
                parameters = json.load(file)
                activity_percent = calculate_activity(activity_dict[nickname], [event.value for event in EventType if event.name in parameters['BOSSES_ACTIVITY']])
                salary_amount = calculate_salary_by_nickname(activity_dict[nickname], [event.value for event in EventType if event.name in parameters['BOSSES_SALARY']])
                print(activity_percent)
                print(salary_amount)
                return activity_percent[nickname], salary_amount[nickname][0]
        except Exception as e:
            logger.error(f"Key:Error ({nickname}) : {e}")




