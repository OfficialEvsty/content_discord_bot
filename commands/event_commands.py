import discord

from services.event_service import EventService


async def save_event(session_generator, event):
    async for session in session_generator:
        service = EventService(session)
        guid = event.guid
        await service.add_events(guid, event)