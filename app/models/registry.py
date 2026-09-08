"""
Registry models.
RegistryType = types of registry entries (contract, offer, disciplinary, etc.)
Registry = progressive counter for documents.
"""
from sqlalchemy import String, Integer, SmallInteger, Boolean, DateTime, Date, ForeignKey, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from datetime import datetime, date
from .base import Base


class RegistryType(Base):
    __tablename__ = 'RegistryTypes'
    __table_args__ = {'schema': 'dbo'}

    RegisterTypeId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    Acronim: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    Description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    NoCopy: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    GenerateDocument: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    CdcMainId: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    PublicRequest: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    registries: Mapped[list['Registry']] = relationship(back_populates='registry_type', lazy='dynamic')


class Registry(Base):
    __tablename__ = 'Registry'
    __table_args__ = {'schema': 'dbo'}

    RegistroId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    CounterPerDocType: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    DocName: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    DocDate: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    DocumentTypeId: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    IsDeleted: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=False)
    DateSys: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, default=func.getdate(), server_default=func.getdate())
    IussedBy: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    EmployeerId: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('dbo.Employeers.EmployeerId'), nullable=True)
    RegistryTypeId: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('dbo.RegistryTypes.RegisterTypeId'), nullable=True)
    Accessid: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    Nota: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    registry_type: Mapped[Optional['RegistryType']] = relationship(back_populates='registries', lazy='select')
