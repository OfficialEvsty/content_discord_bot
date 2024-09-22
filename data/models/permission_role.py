from sqlalchemy import Column, BigInteger

from data.models.base_model import Entity


class PermissionRole(Entity):
    __tablename__ = "permission_roles"
    admin_role_id = Column(BigInteger)
    moder_role_id = Column(BigInteger)