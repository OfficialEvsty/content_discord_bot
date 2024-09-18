import json

import discord

with open('roles_permissions.json') as f:
    perms_config = json.load(f)

permissions = perms_config["permissions"]
roles = perms_config["roles"]
allowed_users = perms_config["admin_user_ids"]

# Проверка прав
def user_has_permission(user: discord.Member, permission):
    user_roles = user.roles
    user_role_ids = [role.id for role in user_roles]
    user_id = user.id
    required_roles = permissions.get(permission, [])
    is_accessed = user_id in allowed_users or any(roles[role_name] in user_role_ids for role_name in required_roles)
    return is_accessed