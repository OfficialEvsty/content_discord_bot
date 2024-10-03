import json
from collections import defaultdict
from typing import Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from data.models.event import Activity, EventType
from data.models.nickname import Nickname

with open('commands/calculating/parameters.json') as file:
    config = json.load(file)

async def collect_activities_by_nickname(activities):
    activity_percentage_dict = {}
    temp = set()
    for activity in activities:
        activity_percentage_dict.setdefault(activity.nickname, []).append(activity)

        temp.add(activity.event_id)

    # for name, visit_count in activity_percentage_dict.items():
    #     activity_percentage_dict[name] = round(visit_count / activity_boss_quantity, 2) * 100
    return activity_percentage_dict

def calculate_activity(activity_dict: Dict[Nickname, List[Activity]], chosen_events: List[str]):
    uniq_events_counter = set()
    filtered_dict: Dict[Nickname, List[Activity]] = {}
    for nickname, activities in activity_dict.items():
        actual_activities = []
        for activity in activities:
            if activity.event.type.value in chosen_events:
                uniq_events_counter.add(activity.event_id)
                actual_activities.append(activity)
        filtered_dict.setdefault(nickname, []).extend(actual_activities)

    activity_percent_dict: Dict[str, int] = {}
    filtered_events_count = len(uniq_events_counter)
    for nickname, filtered_activities in filtered_dict.items():
        if filtered_events_count > 0:
            activity_percent_dict[nickname.name] = round((len(filtered_activities) / filtered_events_count) * 100, 2)
        else:
            activity_percent_dict.setdefault(nickname.name, 0)

    return activity_percent_dict



