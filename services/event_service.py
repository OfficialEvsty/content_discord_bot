import logging
from datetime import datetime
from typing import List

from sqlalchemy import delete, select, and_, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, contains_eager

from data.models.event import Event, Activity

logger = logging.getLogger("app.services")
class EventService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_events(self, events):
        """
        Асинхронный метод для добавления или обновления одного или более никнеймов.

        :param nicknames: Список строк (никнеймов) для добавления или обновления.
        """
        if not isinstance(events, list):
            events = [events]  # Превращаем в список, если один никнейм


        # Добавляем или обновляем пользователей
        for event in events:
            logger.debug(f"Добавляем новое событие: {event}")
            self.session.add(event)

        # Сохраняем изменения в базе данных
        await self.session.commit()
        logger.info(f"События были добавлены в БД: {events}")

    async def delete_events(self, guid, event_ids):
        if not isinstance(event_ids, list):
            event_ids = [event_ids]  # Превращаем в список, если один никнейм
        # Удаление пользователей с никнеймами из списка
        await self.session.execute(
            delete(Event).where(and_(Event.id.in_(event_ids), Event.guid == guid))
        )

        # Применяем изменения в базе данных
        await self.session.commit()
        logger.info(f"Ивенты были удалены из БД с id:{event_ids}")

    async def get_events(self, guid, event_ids=None):
        try:
            result = None
            if id is None:
                try:
                    result = await self.session.execute(select(Event).where(Event.guid == guid))
                except Exception as e:
                    logger.error(f"Ошибка при попытке получить все события: {e}")
            else:
                try:
                    result = await self.session.execute(select(Event).where(
                    and_(
                        Event.id.in_(event_ids),
                        Event.guid == guid
                    )))
                except Exception as e:
                    logger.error(f"Ошибка при попытке получить события по id: {e}")
            events = result.scalars()
            return events
        except Exception as e:
            logger.error(f"Ошибка при попытке получить события из БД")

    async def add_activities(self, activities: List[Activity]):
        self.session.add_all(activities)
        await self.session.commit()

    async def get_activities(self, guid, start_date, end_date, nickname_ids = None) -> Sequence[Activity]:
        try:
            if start_date is None or end_date is None:
                result = await self.session.execute(select(
                    select(Activity)
                    .options(joinedload(Activity.event))
                    .join(Event)
                    .where(Activity.guid == guid)))
                activities = result.scalars().all()
                return activities
            start = start_date.date()
            end = end_date.date()
            if nickname_ids is None:
                result = await self.session.execute(select(
                    select(Activity)
                    .options(joinedload(Activity.event))
                    .join(Event)
                    .where(
                        and_(
                            Activity.guid == guid,
                            Event.datetime.between(start, end)
                        )
                    )
                ))
            else:
                result = await self.session.execute(
                    select(Activity)
                    .options(joinedload(Activity.event))
                    .join(Event)
                    .where(
                        and_(
                            Activity.nickname_id.in_(nickname_ids),
                            Activity.guid == guid,
                            Event.datetime.between(start, end)
                        )
                    )
                )
            activities = result.scalars().all()
            return activities
        except Exception as e:
            logger.error(f"Ошибка при получении активностей: {e}")
