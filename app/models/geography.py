from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from .base import Base

class Continent(Base):
    __tablename__ = 'Continents'
    __table_args__ = {'schema': 'Geo'}

    ContinentId: Mapped[int] = mapped_column(Integer, primary_key=True)
    ContinentName: Mapped[Optional[str]] = mapped_column(String(30))

    nations: Mapped[List['Nation']] = relationship(back_populates='continent', lazy='dynamic')

class Nation(Base):
    __tablename__ = 'Nations'
    __table_args__ = {'schema': 'Geo'}

    NationId: Mapped[int] = mapped_column(Integer, primary_key=True)
    ContinentId: Mapped[Optional[int]] = mapped_column(ForeignKey('Geo.Continents.ContinentId'))
    NationName: Mapped[Optional[str]] = mapped_column(String(50))
    NationCode: Mapped[Optional[str]] = mapped_column(String(3))

    continent: Mapped[Optional['Continent']] = relationship(back_populates='nations', lazy='select')
    counties: Mapped[List['County']] = relationship(back_populates='nation', lazy='dynamic')

class County(Base):
    __tablename__ = 'Counties'
    __table_args__ = {'schema': 'Geo'}

    CountyId: Mapped[int] = mapped_column(Integer, primary_key=True)
    NationId: Mapped[Optional[int]] = mapped_column(ForeignKey('Geo.Nations.NationId'))
    CountyName: Mapped[Optional[str]] = mapped_column(String(50))
    CountyCode: Mapped[Optional[str]] = mapped_column(String(5))

    nation: Mapped[Optional['Nation']] = relationship(back_populates='counties', lazy='select')
    towns: Mapped[List['Town']] = relationship(back_populates='county', lazy='dynamic')

class Town(Base):
    __tablename__ = 'Towns'
    __table_args__ = {'schema': 'Geo'}

    TownId: Mapped[int] = mapped_column(Integer, primary_key=True)
    CountyId: Mapped[Optional[int]] = mapped_column(ForeignKey('Geo.Counties.CountyId'))
    TownName: Mapped[Optional[str]] = mapped_column(String(50))

    county: Mapped[Optional['County']] = relationship(back_populates='towns', lazy='select')
