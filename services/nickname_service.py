from datetime import datetime
from typing import List, Sequence

from sqlalchemy import select, delete, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from data.models.member import NicknameOwner, ArchivedNickname
from data.models.nickname import Nickname

logger = logging.getLogger("app.services")
class NicknameService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_or_update_nicknames(self, guid, nicknames):
        """
        Асинхронный метод для добавления или обновления одного или более никнеймов.

        :param nicknames: Список строк (никнеймов) для добавления или обновления.
        """
        if not isinstance(nicknames, list):
            nicknames = [nicknames]  # Превращаем в список, если один никнейм

        # Ищем существующие записи с указанными никнеймами
        existing_nicks = await self.session.execute(
            select(Nickname).filter(and_(Nickname.name.in_(nicknames), Nickname.guid==guid))
        )
        existing_nicks = existing_nicks.scalars().all()

        # Словарь для быстрого поиска существующих пользователей
        existing_nicknames = {nick.name: nick for nick in existing_nicks}

        # Добавляем или обновляем пользователей
        for nickname in nicknames:
            if nickname not in existing_nicknames:
                logger.debug(f"Добавляем новый ник: {nickname} на сервере guid: {guid}")
                new_nick = Nickname(guid=guid, name=nickname, is_borrowed=False, is_archived=False)
                self.session.add(new_nick)

        # Сохраняем изменения в базе данных
        await self.session.commit()
        logger.info(f"Ники были добавлены/обновлены в БД: {existing_nicknames}")

    async def delete_nicknames(self, guid, nicknames):
        if not isinstance(nicknames, list):
            nicknames = [nicknames]  # Превращаем в список, если один никнейм
        # Удаление пользователей с никнеймами из списка
        await self.session.execute(
            delete(Nickname).where(Nickname.name.in_(nicknames) and Nickname.guid == guid)
        )

        # Применяем изменения в базе данных
        await self.session.commit()
        logger.info(f"Ники были удалены из БД: {nicknames}")

    async def get_nicknames(self, guid, substring=""):
        try:
            result = await self.session.execute(select(Nickname).where(
                and_(
                    Nickname.name.like(f'%{substring}%'),
                    Nickname.guid == guid,
                    Nickname.is_archived == False
                )
            ))
            nicknames = result.scalars().all()
            return nicknames
        except Exception as e:
            logger.error(f"Ошибка при попытке получить доступные никнеймы: {e}")
            await self.session.close()

    async def get_ids(self, guid, nicknames: []) -> List[int]:
        try:
            result = await self.session.execute(select(Nickname)
                .where(
                    and_(
                        Nickname.name.in_(nicknames),
                        Nickname.guid == guid,
                        Nickname.is_archived == False
                    )
            ))
            names = result.scalars().all()
            return [name.id for name in names]

        except Exception as e:
            logger.error(f"Ошибка при попытке получить id ников: {e}")
            await self.session.close()

    async def get_owned_nicknames(self, guid, user_id) -> Sequence[Nickname]:
        try:
            result = await self.session.execute(select(Nickname)
                .join(NicknameOwner)
                    .where(
                        and_(
                            Nickname.guid == guid,
                            NicknameOwner.user_id == user_id
                        )
                    )
            )
            nicknames = result.scalars().all()
            return nicknames
        except Exception as e:
            logger.error(f"Ошибка в методе {self.get_owned_nicknames} в сервисе: {self}: {e}")
            await self.session.close()

    async def bound_nickname(self, guid, user_id, nickname: Nickname, is_archived = False):
        try:
            transfer_activities = []
            await self.session.refresh(nickname, ['nickname_owner', 'archived_nickname', 'activities'])
            # Поиск актуального никнейма для пользователя, если тот существовал прежде
            result = await self.session.execute(select(Nickname)
                .join(NicknameOwner)
                    .filter(and_(
                        Nickname.is_archived == is_archived,
                        NicknameOwner.user_id == user_id,
                        NicknameOwner.guid == guid
                    )
                )
            )
            if result:

                nickname_to_archive_list = result.scalars().all()
                if len(nickname_to_archive_list) > 0:
                    nickname_to_archive = nickname_to_archive_list[0]
                    if nickname_to_archive.id == nickname.id and nickname_to_archive.guid == nickname.guid:
                        raise Exception(f"Нельзя сменить старый никнейм на тот же самый")
                    await self.session.refresh(nickname_to_archive, ['nickname_owner', 'archived_nickname', 'activities'])
                    transfer_activities = nickname_to_archive.activities
                    nickname_to_archive.is_archived = True
                    nickname_to_archive.archived_nickname = ArchivedNickname(archived_at=datetime.now(),
                                                                             nickname_id=nickname_to_archive.id,
                                                                             guid=guid)
                    logger.debug(f"{nickname_to_archive} помещен в архив")
            if nickname.nickname_owner:
                logger.debug(f"{nickname.nickname_owner} уже существует в БД")
                nickname.nickname_owner = NicknameOwner(user_id=user_id, nickname_id=nickname.id, guid=guid)
                logger.debug(f"Владелец {nickname.nickname_owner} обновлен для ника {nickname.name} на сервере {guid}")
            else:
                owner = NicknameOwner(user_id=user_id, nickname_id=nickname.id, guid=guid)
                self.session.add(owner)

                logger.debug(f"Добавляем нового владельца {owner} для ника: {nickname} на сервере guid: {guid}")
            nickname.is_borrowed = True

            logger.debug(
                f"Переносим активности со старого аккаунта: {transfer_activities} на новый {nickname} на сервере guid: {guid}")
            event_ids_2 = {activity.event_id for activity in nickname.activities}

            # Фильтруем список activities_1, исключая те, у которых event_id есть в activities_2
            filtered_activities = [activity for activity in transfer_activities if activity.event_id not in event_ids_2]
            nickname.activities.extend(filtered_activities)

            await self.session.commit()
            await self.session.close()
        except Exception as e:
            logger.error(f"Ошибка во время привязки никнейма {nickname} к игроку {user_id}: {e}")
            await self.session.close()
            return

