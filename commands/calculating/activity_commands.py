import json
from collections import defaultdict
from datetime import date
from time import strptime
from typing import Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from data.models.event import Activity, EventType, Event
from data.models.nickname import Nickname

with open('commands/calculating/parameters.json') as file:
    config = json.load(file)

async def collect_activities_by_nickname(activities):
    activity_percentage_dict = {}
    for activity in activities:
        activity_percentage_dict.setdefault(activity.nickname, []).append(activity)

    # for name, visit_count in activity_percentage_dict.items():
    #     activity_percentage_dict[name] = round(visit_count / activity_boss_quantity, 2) * 100
    return activity_percentage_dict

def calculate_activity(activity_dict: Dict[Nickname, List[Activity]], chosen_events: List[str], date_key: (int, int) = None):
    uniq_events_counter = set()
    filtered_dict: Dict[Nickname, List[Activity]] = {}
    for nickname, activities in activity_dict.items():
        actual_activities = []
        for activity in activities:
            if activity.event.type.value in chosen_events:
                if date_key is not None:
                    event_date: date = activity.event.datetime.date()
                    if event_date.month != date_key[0] or event_date.year != date_key[1]:
                        continue
                uniq_events_counter.add(activity.event_id)
                actual_activities.append(activity)
        filtered_dict.setdefault(nickname, []).extend(actual_activities)

    activity_percent_dict: Dict[str, float] = {}
    filtered_events_count = len(uniq_events_counter)
    for nickname, filtered_activities in filtered_dict.items():
        if filtered_events_count > 0:
            activity_percent_dict[nickname.name] = round((len(filtered_activities) / filtered_events_count) * 100, 2)
        else:
            activity_percent_dict.setdefault(nickname.name, 0)

    return activity_percent_dict


def get_activity_entries(activities: List[tuple[Activity, float]]) -> List[str]:
    activity_entries: [str] = []
    for t in activities:
        event: Event = t[0].event
        activity_entries.append(f"`{event.type.value.center(15)}` |"
                                f" `{str(event.datetime.strftime('День %d, %H:%M')).center(14)}` |"
                                f" `{str(0).rjust(7) if t[1] == 0 else str(round(t[1], 2)).rjust(7)}`")

    return activity_entries










