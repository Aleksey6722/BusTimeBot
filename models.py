from sqlalchemy import create_engine, String, Integer, Float, Column
from sqlalchemy.orm import Session, declarative_base


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
    data = Column(String(256), nullable=False)

if __name__ == '__main__':
    Base.metadata.create_all(engine)
