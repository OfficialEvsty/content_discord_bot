from sqlalchemy import Integer, Column, ForeignKey, DateTime, BigInteger
from sqlalchemy.orm import relationship

from .base_model import Entity

# NicknameOwner хранит зависимости актуальных и старых Nickname(ов) пользователей(из Archeage)
class NicknameOwner(Entity):
    __tablename__ = 'nickname_owners'

    user_id = Column(BigInteger)
    nickname_id = Column(Integer, ForeignKey('nicknames.id'))

    nicknames = relationship("Nickname", back_populates="nickname_owner")

# ArchivedNickname хранит записи о старых Nickname(ах) пользователей(из Archeage)
class ArchivedNickname(Entity):
    __tablename__ = 'archived_nicknames'

    archived_at = Column(DateTime, nullable=False)
    nickname_id = Column(Integer, ForeignKey('nicknames.id'))
    nickname = relationship("Nickname", back_populates="archived_nickname")
