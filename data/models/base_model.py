from sqlalchemy import Column, Integer, String, BigInteger
from sqlalchemy.orm import declarative_base

Base = declarative_base()
class Entity(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)
    guid = Column(BigInteger)

class NamedEntity(Entity):
    __abstract__ = True
    name = Column(String)
