import json
from typing import Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from data.models.event import Activity, Event
from data.models.nickname import Nickname

with open("commands/calculating/parameters.json") as file:
    param = json.load(file)

def calculate_salary_by_nickname(activities_by_nickname: Dict[Nickname, List[Activity]], chosen_bosses) -> (Dict[str, int], float):
    salary_by_nickname: Dict[str, int] = {}
    bank_coffers = 0
    for nickname, activities in activities_by_nickname.items():
        for activity in activities:
            salary_by_nickname.setdefault(nickname.name, 0)
            event: Event = activity.event
            event_type = event.type
            if event_type.value in chosen_bosses:
                if event_type.name in param['SALARY']:
                    event_value = param['SALARY'][event_type.name]
                    event_visits = len(event.activities)
                    unit_value = event_value / event_visits
                    salary_by_nickname[nickname.name] += unit_value * (1 - param['BANK']['Percentage'])
                    bank_coffers += unit_value * param['BANK']['Percentage']

    return salary_by_nickname, bank_coffers

