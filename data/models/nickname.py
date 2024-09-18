from sqlalchemy import Boolean, Column
from sqlalchemy.orm import relationship

from data.models.base_model import NamedEntity

# Nickname хранит данные об имеющихся никнеймах на сервере и их доступность
class Nickname(NamedEntity):
    __tablename__ = 'nicknames'

    is_borrowed = Column(Boolean, default = False)
    is_archived = Column(Boolean, default = False)

    nickname_owner = relationship("NicknameOwner", back_populates="nicknames", uselist=False, cascade="all, delete-orphan")
    archived_nickname = relationship("ArchivedNickname", back_populates="nickname", uselist=False)
    activities = relationship("Activity", back_populates="nickname")