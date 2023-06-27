from sqlalchemy import create_engine, String, Integer, Float, Column, BigInteger, func, DateTime, Time
from sqlalchemy.orm import Session, declarative_base
import time


engine = create_engine("postgresql+psycopg2://postgres:sql123@localhost/busbot")
session = Session(bind=engine)
Base = declarative_base()


class Region(Base):
    __tablename__ = 'region'
    id = Column(Integer, primary_key=True, autoincrement=True)
    latitude1 = Column(Float, nullable=False)
    longitude1 = Column(Float, nullable=False)
    latitude2 = Column(Float, nullable=False)
    longitude2 = Column(Float, nullable=False)
    name = Column(String(100), nullable=False)


class TramStop(Base):
    __tablename__ = 'tramstop'
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)


class Button(Base):
    __tablename__ = 'button'
    id = Column(Integer, primary_key=True)
    key = Column(String(64), nullable=False)
    name = Column(String(64), nullable=False)
    stop_id = Column(String(256), nullable=False)
    bus_number = Column(String(64), nullable=True)
    day = Column(String(10), nullable=True)
    date = Column(DateTime(), server_default=func.now())


class Notice(Base):
    __tablename__ = 'notice'
    id = Column(Integer, primary_key=True)
    username = Column(String(64), nullable=False)
    chat_id = Column(Integer, nullable=False)
    stop_id = Column(String(256), nullable=False)
    stop_name = Column(String(64), nullable=False)
    bus_number = Column(String(64), nullable=False)
    day = Column(String(10), nullable=True)
    notice_time = Column(Time())

if __name__ == '__main__':
    Base.metadata.create_all(engine)
