import json

import discord
from sqlalchemy.ext.asyncio import AsyncSession

from commands.permission_commands import get_permission_roles

with open('roles_permissions.json') as f:
    perms_config = json.load(f)

permissions = perms_config["permissions"]
role_names = perms_config["roles"]
allowed_users = perms_config["admin_user_ids"]

# Проверка прав
async def user_has_permission(session: AsyncSession, user: discord.Member, permission):
    user_roles = user.roles
    user_role_ids = [role.id for role in user_roles]
    user_id = user.id
    permission_role = await get_permission_roles(session, user.guild.id)
    is_role_accessed = False
    if permission_role:
        roles = {role_names[0]: permission_role.admin_role_id, role_names[1]: permission_role.moder_role_id}
        required_roles = permissions.get(permission, [])
        is_role_accessed = any(roles[role_name] in user_role_ids for role_name in required_roles)
    is_accessed = user_id in allowed_users or is_role_accessed
    return is_accessed