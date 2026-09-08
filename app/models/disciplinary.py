"""
Disciplinary History model.
Tracks employee disciplinary actions (referats).
"""
from sqlalchemy import String, Integer, SmallInteger, DateTime, Date, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from datetime import datetime, date
from .base import Base


class EmployeeDisciplinaryHistory(Base):
    __tablename__ = 'EmployeeDisciplinaryHistory'
    __table_args__ = {'schema': 'dbo'}

    EmployeeDisciplinaryHistoryId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    EmployeeHireHistoryId: Mapped[int] = mapped_column(Integer, ForeignKey('dbo.EmployeeHireHistory.EmployeeHireHistoryId'), nullable=False)
    RegistroId: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('dbo.Registry.RegistroId'), nullable=True)
    DocSavedOn: Mapped[Optional[str]] = mapped_column(String(250), nullable=True)
    DateSys: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, default=func.getdate(), server_default=func.getdate())
    ExplicationNote: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    DisciplinaryCommDecizion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    CommDisciplinaryId: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    ArticoloLegaleId: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    SefID: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    DataAvvenimento: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    OraAvvenimento: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    ConvocareRegistryId: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    DocumentPerJobContractId: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
