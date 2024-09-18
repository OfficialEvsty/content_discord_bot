from sqlalchemy import Column, BigInteger

from data.models.base_model import Base

class Setting(Base):
    __tablename__ = 'settings'

    guid = Column(BigInteger, primary_key=True)
    redirect_channel_id = Column(BigInteger)
    request_channel_id = Column(BigInteger)