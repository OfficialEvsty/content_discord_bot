import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data.models.permission_role import PermissionRole

logger = logging.getLogger("app.commands")

async def set_permission_roles(session: AsyncSession, guid, admin_role_id, moder_role_id = None):
    try:
        result = await session.execute(select(PermissionRole).where(PermissionRole.guid == guid))
        existing_permission = result.scalars().first()
        if existing_permission:
            existing_permission.moder_role_id = moder_role_id
            existing_permission.admin_role_id = admin_role_id
        else:
            permission = PermissionRole(guid=guid, admin_role_id=admin_role_id, moder_role_id=moder_role_id)
            session.add(permission)
        await session.commit()
    except Exception as e:
        logger.error(f"Ошибка во время обращения к БД для записи id ролей: {e}")

async def get_permission_roles(session: AsyncSession, guid: int) -> PermissionRole:
    try:
        result = await session.execute(select(PermissionRole).where(PermissionRole.guid == guid))
        return result.scalars().first()
    except Exception as e:
        logger.error(f"Ошибка во время обращения к БД для получения id ролей: {e}")