from sqlalchemy import *
from sqlalchemy import Column, Date, Integer, String
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy.dialects import postgresql, mysql, mssql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

import DbConnection

Base = declarative_base()
engine = DbConnection.create_shelly_engine()


class Device(Base):
    """"""
    __tablename__ = "Device"

    dbid = Column(Integer, primary_key=True)
    id = Column(String(30), nullable=False)
    model = Column(String(20), nullable=False)
    mac = Column(String(30))
    ip = Column(String(40))
    name = Column(String(40), nullable=True)
    autoTurnOff = Column(BOOLEAN, nullable=False, default=True)

    series = relationship("Channel", foreign_keys='Channel.dbIdDevice', back_populates="device")

    # ----------------------------------------------------------------------
    def __init__(self, id, model, mac, ip, name):
        """"""
        self.id = id
        self.model = model
        self.mac = mac
        self.ip = ip
        self.name = name


class Channel(Base):
    """"""
    __tablename__ = "Channel"

    dbid = Column(Integer, primary_key=True)
    dbIdDevice = Column(Integer, ForeignKey(Device.dbid), nullable=False)
    channelId = Column(Integer, nullable=False)
    turnOffThreshold = Column(Integer, nullable=False, default=10)
    turnOffTimeout = Column(Integer, nullable=False, default=30)
    doNotTurnOffBelow = Column(Float, nullable=False, default=0.2)

    # ----------------------------------------------------------------------
    def __init__(self, device, channelId, energy):
        """"""
        self.device = device
        self.channelId = channelId
        self.energy = energy


Base.metadata.create_all(engine)
