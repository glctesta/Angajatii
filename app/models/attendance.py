from sqlalchemy import String, Integer, SmallInteger, Boolean, DateTime, ForeignKey, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from datetime import datetime
from .base import Base

class Shift(Base):
    __tablename__ = 'Shifts'
    __table_args__ = {'schema': 'dbo'}

    ShiftId: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    Shift: Mapped[str] = mapped_column(String(20), nullable=False)

    timetables: Mapped[List['ShiftTimeTable']] = relationship(back_populates='shift', lazy='dynamic')

class ShiftTimeTable(Base):
    __tablename__ = 'ShiftTimeTable'
    __table_args__ = {'schema': 'dbo'}

    ShiftsTimeTableId: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    ShiftId: Mapped[int] = mapped_column(ForeignKey('dbo.Shifts.ShiftId'), nullable=False)
    TimeRange: Mapped[Optional[str]] = mapped_column(String(50))
    Note: Mapped[Optional[str]] = mapped_column(String(100))

    shift: Mapped['Shift'] = relationship(back_populates='timetables', lazy='select')

class Badge(Base):
    __tablename__ = 'Badges'
    __table_args__ = {'schema': 'dbo'}

    BadgeId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    NoBadge: Mapped[str] = mapped_column(String(15), nullable=False)
    EhxBadge: Mapped[Optional[str]] = mapped_column(String(15))
    SerialBadge: Mapped[Optional[str]] = mapped_column(String(30))
    DateIn: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.getdate(), server_default=func.getdate())
    DateOut: Mapped[Optional[datetime]] = mapped_column(DateTime)
    EmployeerId: Mapped[Optional[int]] = mapped_column(ForeignKey('dbo.Employeers.EmployeerId'))
    NotForEmployee: Mapped[Optional[bool]] = mapped_column(Boolean)
    ForGuest: Mapped[Optional[bool]] = mapped_column(Boolean)

    badge_history: Mapped[List['EmployeeBadgeHistory']] = relationship(back_populates='badge', lazy='dynamic')

class EmployeeBadgeHistory(Base):
    __tablename__ = 'EmployeeBadgeHistory'
    __table_args__ = {'schema': 'dbo'}

    EmployeeBadgeHistoryId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    EmployeeHireHistoryId: Mapped[int] = mapped_column(ForeignKey('dbo.EmployeeHireHistory.EmployeeHireHistoryId'), nullable=False)
    BadgeID: Mapped[int] = mapped_column(ForeignKey('dbo.Badges.BadgeId'), nullable=False)
    DateIn: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.getdate(), server_default=func.getdate())
    DateOut: Mapped[Optional[datetime]] = mapped_column(DateTime)

    badge: Mapped['Badge'] = relationship(back_populates='badge_history', lazy='select')
