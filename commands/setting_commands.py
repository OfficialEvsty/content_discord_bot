from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data.models.setting import Setting
import logging

logger = logging.getLogger("app.commands")

async def set_text_channels(session: AsyncSession, guid, redirect_channel_id, request_channel_id):
    try:
        result = await session.execute(select(Setting).where(Setting.guid == guid))
        if result:
            existing_setting = result.scalars().first()
            existing_setting.request_channel_id = request_channel_id
            existing_setting.redirect_channel_id = redirect_channel_id
        else:
            setting = Setting(guid=guid, redirect_channel_id=redirect_channel_id, request_channel_id=request_channel_id)
            session.add(setting)
        await session.commit()
    except Exception as e:
        logger.error(f"Ошибка во время обращения к БД для записи id текстовых каналов: {e}")


async def get_redirect_channel_id(session, guid):
    try:
        result = await session.execute(select(Setting).where(Setting.guid == guid))
        setting = result.scalars().first()
        return setting.redirect_channel_id
    except Exception as e:
        logger.error(f"Ошибка во время обращения к БД для получения канала переадрессации: {e}")


async def get_request_channel_id(session, guid):
    try:
        result = await session.execute(select(Setting).where(Setting.guid == guid))
        setting = result.scalars().first()
        return setting.request_channel_id
    except Exception as e:
        logger.error(f"Ошибка во время обращения к БД для получения канала генерации запросов: {e}")