from datetime import date
from typing import Dict, List

from discord.ui import Button, Select

from data.models.event import Activity
from ui.views.base_view import CancelledView



class UserStatisticsView(CancelledView):
    # Словарь активностей, разбитый по датам год-месяц
    activity_by_dates: Dict[(int, int), List[Activity]] = {}
    page_size = 20
    # Ключевое поле для выбора активностей
    current_date_key: (int, int) = None
    def __init__(self, activities):
        super().__init__()
        self.activities = activities

        # ПОДГОТОВКА ДАННЫХ
        self.prepare_activity_data()

        self.current_page = 0
        self.show_activity_button = Button(label="Активность", row=0)
        self.show_salary_button = Button(label="Зарплата", row=0)
        self.prev_button = Button(emoji=":arrow_left:", row=0)
        self.next_button = Button(emoji=":arrow_right:", row=0)
        self.month_selector = Select(row=1)
        self.year_selector = Select(row=2)

    def prepare_activity_data(self):
        for activity in self.activities:
            activity_date: date = activity.event.datetime.date()
            activity_date_key = (activity_date.month, activity_date.year)
            if activity_date_key not in self.activity_by_dates.keys():
                self.activity_by_dates.setdefault(activity_date_key, [])
            self.activity_by_dates[activity_date_key].append(activity)
        print(self.activity_by_dates)


    def select_date_key(self):
        last_year = max([keyTuple[1] for keyTuple in self.activity_by_dates.keys()])
        last_month = max([keyTuple[0] for keyTuple in self.activity_by_dates.keys() if keyTuple[1] == last_year])
        self.current_date_key = (last_month, last_year)

    def update_ui(self):
        available_activities = self.activity_by_dates[self.current_date_key]
        start_index = self.current_page * self.page_size
        end_index = min(start_index + self.page_size, start_index + (len(available_activities) - start_index))
        activity_page = available_activities[start_index:end_index]


    def init_ui(self):
        pass

