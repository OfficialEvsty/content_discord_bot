import json
from datetime import date
from typing import Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from data.models.event import Activity, Event
from data.models.nickname import Nickname

with open("commands/calculating/parameters.json") as file:
    param = json.load(file)

def calculate_salary_by_nickname(activities_by_nickname: Dict[Nickname, List[Activity]], chosen_bosses, date_key: (int, int) = None) -> (Dict[str, int], float):
    salary_by_nickname: Dict[str, int] = {}
    bank_coffers = 0
    event_counter_dict: Dict[Event, int] = {}
    for _, activities in activities_by_nickname.items():
        for activity in activities:
            event_counter_dict.setdefault(activity.event, 0)
            event_counter_dict[activity.event] += 1
    for nickname, activities in activities_by_nickname.items():
        for activity in activities:
            salary_by_nickname.setdefault(nickname.name, 0)
            event: Event = activity.event
            event_type = event.type
            if event_type.value in chosen_bosses:
                if date_key is not None:
                    event_date: date = activity.event.datetime.date()
                    if event_date.month != date_key[0] or event_date.year != date_key[1]:
                        continue
                if event_type.name in param['SALARY']:
                    event_value = param['SALARY'][event_type.name]
                    event_visits = event_counter_dict[event]
                    unit_value = event_value / event_visits
                    salary_by_nickname[nickname.name] += unit_value * (1 - param['BANK']['Percentage'])
                    bank_coffers += unit_value * param['BANK']['Percentage']

    return salary_by_nickname, bank_coffers

def get_calculated_salary_activities(nickname: str, all_activities_for_chosen_dates: List[Activity]):
    payments: List[tuple[Activity, float]] = []
    bank_coffers = 0
    event_counter_dict: Dict[Event, int] = {}
    for activity in all_activities_for_chosen_dates:
        event_counter_dict.setdefault(activity.event, 0)
        event_counter_dict[activity.event] += 1
    for activity in all_activities_for_chosen_dates:
        event = activity.event
        event_type = event.type
        if activity.nickname.name != nickname:
            continue
        if event_type.name in param['SALARY']:
            event_value = param['SALARY'][event_type.name]
            event_visits = event_counter_dict[event]
            unit_value = event_value / event_visits
            payments.append((activity, unit_value * (1 - param['BANK']['Percentage'])))
            bank_coffers += unit_value * param['BANK']['Percentage']
        else:
            payments.append((activity, 0))

    return payments, bank_coffers