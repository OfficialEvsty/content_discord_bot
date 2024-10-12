import json
from datetime import date, datetime
from math import ceil
from typing import Dict, List
import locale
import discord
from discord import SelectOption
from discord.ui import Button, Select

from commands.calculating.activity_commands import get_activity_entries, calculate_activity
from commands.calculating.salary_commands import calculate_salary_by_nickname, get_calculated_salary_activities
from data.configuration import CONFIGURATION
from data.models.event import Activity, EventType
from data.models.nickname import Nickname
from ui.embeds.owner_nicknames_profile_embed import BoundingNicknameAndActivityEmbed, BoundingNicknamesEmbed
from ui.views.base_view import CancelledView

parameters = None
with open('commands/calculating/parameters.json') as file:
    parameters = json.load(file)


class UserStatisticsView(CancelledView):
    # Словарь активностей, разбитый по датам год-месяц
    salary_calculated_activities_by_current_nickname: List[tuple[Activity, int]] = None
    activity_by_dates: Dict[tuple[int, int], List[Activity]] = {}
    available_activity_entries: List[Activity]
    page_size = 15
    salary: float = 0
    activity: float = 0
    coffers: float = 0
    # Ключевое поле для выбора активностей
    current_date_key: tuple[int, int] = None
    def __init__(self, user: discord.Member, nickname: Nickname, previous_nicknames, nickname_activities, message: discord.Message = None):
        super().__init__()
        self.user = user
        self.previous_nicknames = previous_nicknames
        self.nickname = nickname
        self.nickname_activities = nickname_activities
        self.message = message

        # ПОДГОТОВКА ДАННЫХ
        self.prepare_activity_data()


        self.current_page = 0
        self.prev_button = Button(label="Предыдущая")
        self.prev_button.callback = self.prev
        self.next_button = Button(label="Следующая")
        self.next_button.callback = self.next

        self.month_selector = Select(placeholder="Выберите месяц")
        self.month_selector.disabled = True
        self.month_selector.callback = self.on_select_date
        self.year_selector = Select(placeholder="Выберите год")
        self.year_selector.disabled = True
        self.year_selector.callback = self.on_select_date
        self.select_date_key()
        self.update_controls()

    def prepare_activity_data(self):
        if self.nickname not in self.nickname_activities:
            return
        activities_dict = self.nickname_activities
        for nickname, activities in activities_dict.items():
            for activity in activities:
                activity_date: date = activity.event.datetime.date()
                activity_date_key = (activity_date.month, activity_date.year)
                if activity_date_key not in self.activity_by_dates.keys():
                    self.activity_by_dates.setdefault(activity_date_key, [])
                activity.nickname = nickname
                self.activity_by_dates[activity_date_key].append(activity)

    def translate_bosses_names(self, names: List[str]):
        return [event.value for name in names for event in EventType if name == event.name]


    def select_date_key(self):
        last_year = max([keyTuple[1] for keyTuple in self.activity_by_dates.keys()])
        last_month = max([keyTuple[0] for keyTuple in self.activity_by_dates.keys() if keyTuple[1] == last_year])
        if not self.year_selector.disabled:
            last_year = int(self.year_selector.values[0])
        if not self.month_selector.disabled:
            last_month = int(self.month_selector.values[0])
        self.current_date_key = (last_month, last_year)
        self.available_activity_entries = self.activity_by_dates[self.current_date_key]
        self.salary_calculated_activities_by_current_nickname, _ = get_calculated_salary_activities(self.nickname.name,
                                                                                      self.available_activity_entries)

        activity_dict = calculate_activity(self.nickname_activities, self.translate_bosses_names(parameters['BOSSES_ACTIVITY']),
                                           self.current_date_key)
        salary_dict, coffers = calculate_salary_by_nickname(self.nickname_activities, self.translate_bosses_names(parameters['BOSSES_SALARY']),
                                                            self.current_date_key)
        print(f"дикты {activity_dict}, {salary_dict}")
        self.activity = activity_dict[self.nickname.name]
        self.salary = salary_dict[self.nickname.name]


    async def next(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'])
        self.current_page += 1
        self.update_controls()
        await self.update_ui(interaction)

    async def prev(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'])
        self.current_page -= 1
        self.update_controls()
        await self.update_ui(interaction)

    async def on_select_date(self, interaction):
        await interaction.response.defer(ephemeral=CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'])
        self.select_date_key()
        self.current_page = 0
        self.update_controls()
        await self.update_ui(interaction)


    async def update_ui(self, interaction: discord.Interaction):
        start_index = self.current_page * self.page_size
        entries_count = len(self.salary_calculated_activities_by_current_nickname)
        end_index = min(start_index + self.page_size, start_index + (entries_count - start_index))

        activity_page = get_activity_entries(self.salary_calculated_activities_by_current_nickname[start_index:end_index])
        formatted_activity_page = [f"{index+1}.\t{activity_page[index]} " for index in range(len(activity_page))]

        embed = BoundingNicknameAndActivityEmbed(self.user, self.nickname.name, self.previous_nicknames, self.activity,
                                                 self.salary, formatted_activity_page, self.current_page+1,
                                                 ceil(entries_count // self.page_size))

        await interaction.followup.edit_message(message_id=self.message.id, embed=embed, view=self)


    locale.setlocale(locale.LC_ALL, "")

    def update_controls(self):
        self.clear_items()
        # Инициализируем все контролы на view
        start_index = self.current_page * self.page_size
        end_index = min(start_index + self.page_size, start_index + (len(self.salary_calculated_activities_by_current_nickname) - start_index))
        self.next_button.disabled = False if end_index < len(self.salary_calculated_activities_by_current_nickname) else True
        self.prev_button.disabled = False if start_index > self.page_size-1 else True
        self.month_selector.options = [SelectOption(label=datetime(year=2000, month=dateKey[0], day=20).strftime(format="%B (%A)"), value=dateKey[0])
                                       for dateKey in self.activity_by_dates.keys()
                                       if dateKey[1] == self.current_date_key[1]]
        uniq_years = set(dateKey[1] for dateKey in self.activity_by_dates.keys())
        self.year_selector.options = [SelectOption(label=str(year), value=year)
                                      for year in uniq_years]
        self.add_item(self.prev_button)
        self.add_item(self.next_button)
        self.month_selector.disabled = True
        self.year_selector.disabled = True
        if len(self.month_selector.options) > 1:
            self.month_selector.disabled = False
            self.add_item(self.month_selector)
        if len(self.year_selector.options) > 1:
            self.year_selector.disabled = False
            self.add_item(self.year_selector)
        self.add_item(self.cnl_button)


