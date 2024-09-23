from datetime import datetime
from typing import List

import discord
from sqlalchemy import DateTime, func

from commands.calculating.activity_commands import calculate_activity
from commands.ingame_screenshot_commands import pull_nicknames_from_screenshot
from data.models.event import Event, EventType, Activity
from exceptions.cancel_exception import CancelException
from exceptions.timeout_exception import TimeoutException
from services.event_service import EventService
from services.nickname_service import NicknameService
import logging

from ui.views.event_selector_view import EventSelectorView

logger = logging.getLogger("app.controllers")

class EventAndActivityController:

    async def generate_event(self, interaction: discord.Interaction, session_generator, attachment: discord.Attachment,
                            config):
        try:
            chosen_events = await self.select_events(interaction)
            events = []
            for e_type_name in chosen_events:
                event_guid = interaction.guild.id
                event_type = EventType(e_type_name)
                event_datetime = func.now()
                date = datetime.now()
                event_screen_ref = attachment.url

                event = Event(guid=event_guid, type=event_type, datetime=event_datetime, raid_screen_ref=event_screen_ref)
                events.append(event)

            async for session in session_generator:
                pull_result = await pull_nicknames_from_screenshot(interaction, attachment, session, config['SCREENSHOTS_OCR'])
                nicknames = pull_result[0]
                conflicted_nicknames = pull_result[1]
                manual_choice_nicknames = pull_result[2]
                nickname_service = NicknameService(session)
                nickname_ids = await nickname_service.get_ids(interaction.guild.id, nicknames)

                event_service = EventService(session)
                await event_service.add_events(events)
                event_ids = [event.id for event in events]
                activities = [Activity(guid=interaction.guild.id, event_id=event_id, nickname_id=nickname_id) for event_id in event_ids for nickname_id in nickname_ids]
                await event_service.add_activities(activities)
                return {'events_name': chosen_events, 'event_time': date, 'event_ref': event_screen_ref,
                        'event_size': len(nicknames), 'nicknames_collision': conflicted_nicknames,
                        'nicknames_manual': manual_choice_nicknames}
        except CancelException as e:
            logger.info(f"{e}")
            raise CancelException(e)
        except Exception as e:
            logger.error(f"Ошибка во время работы контроллера {self}: {e}")




    async def get_activities(self, interaction: discord.Interaction, session_generator, start_date: str, end_date: str):
        async for session in session_generator:
            guid = interaction.guild.id
            nickname_service = NicknameService(session)
            nicknames = await nickname_service.get_nicknames(guid)
            event_service = EventService(session)
            ids = [nickname.id for nickname in nicknames]
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            activities = await event_service.get_activities(guid, start, end, ids)

            percentage_activity_dict = await calculate_activity(session, activities)
            nickname_activity_percentage_dict = {nickname.name: percentage for nickname in nicknames for name_id, percentage in percentage_activity_dict.items() if name_id == nickname.id}
            return nickname_activity_percentage_dict

    async def select_events(self, interaction: discord.Interaction) -> List[str]:
        events = []
        event_ask_view = EventSelectorView(events)
        title = f"Выберите от 1 до 4 событий, за которые необходимо загрузить скриншот"
        msg = await interaction.followup.send(embed=discord.Embed(title=title), view=event_ask_view)
        await event_ask_view.wait()
        await msg.delete()
        if len(events) == 0:
            raise TimeoutException(f"Время ожидания {event_ask_view} вышло")

        return events
