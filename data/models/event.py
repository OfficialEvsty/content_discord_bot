from sqlalchemy.orm import relationship

from data.models.base_model import Entity
import enum
from sqlalchemy import Enum, Column, DateTime, String, ForeignKey, Integer


# Enum для перечисления типов активностей
class EventType(enum.Enum):
    RAID_BOSS_0 = "Кракен"
    RAID_BOSS_1 = "Ксанатос"
    RAID_BOSS_2 = "Каллидис"
    RAID_BOSS_3 = "Левиафан"
    RAID_BOSS_4 = "Анталлон"

    RAID_T2_BOSS_0 = "Каллеиль"
    RAID_T2_BOSS_1 = "Авиара"

    WAR_LOCATION_BOSS_0 = "Ашьяра"
    WAR_LOCATION_BOSS_1 = "Глен и Лорея"

    WAR_LOCATION_T2_BOSS_0 = "Т2 Секхмет"
    WAR_LOCATION_T2_BOSS_1 = "Т2 Ашьяра"
    WAR_LOCATION_T2_BOSS_2 = "Т2 Глен и Лорея"

# Event хранит тип события, его время и ссылку на скрин рейда
class Event(Entity):
    __tablename__ = "events"
    type = Column(Enum(EventType))
    datetime = Column(DateTime, nullable=False)
    raid_screen_ref = Column(String, nullable=False)

    activities = relationship("Activity", back_populates="event")

class Activity(Entity):
    __tablename__ = "activities"

    nickname_id = Column(Integer, ForeignKey('nicknames.id'))
    event_id = Column(Integer, ForeignKey('events.id'))

    nickname = relationship("Nickname", back_populates="activities")
    event = relationship("Event", back_populates="activities")