from sqlalchemy import String, Integer, SmallInteger, Boolean, DateTime, ForeignKey, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from datetime import datetime
from .base import Base

class CostCenter(Base):
    __tablename__ = 'CostCenters'
    __table_args__ = {'schema': 'dbo'}

    CdcId: Mapped[int] = mapped_column(Integer, primary_key=True)
    CdcDescription: Mapped[Optional[str]] = mapped_column(String(50))
    Cdc: Mapped[Optional[str]] = mapped_column(String(10))
    CdCNoCiel: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    sub_cdcs: Mapped[List['CdcSub']] = relationship(back_populates='cost_center', lazy='dynamic')

class CdcSub(Base):
    __tablename__ = 'CdcSub'
    __table_args__ = {'schema': 'dbo'}

    SubCdcId: Mapped[int] = mapped_column(Integer, primary_key=True)
    CdcId: Mapped[int] = mapped_column(ForeignKey('dbo.CostCenters.CdcId'), nullable=False)
    SubCdc: Mapped[int] = mapped_column(Integer, nullable=False)
    SubCdcDescription: Mapped[str] = mapped_column(String(50), nullable=False)
    DirectEmployee: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, server_default=text('0'))
    IndirectProduction: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, server_default=text('0'))
    SubCdcNoCiel: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    DefaultCdc: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    PhaseTraceId: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    cost_center: Mapped['CostCenter'] = relationship(back_populates='sub_cdcs', lazy='select')

class FunctionsStructure(Base):
    __tablename__ = 'FunctionsStructure'
    __table_args__ = {'schema': 'dbo'}

    StructureId: Mapped[int] = mapped_column(Integer, primary_key=True)
    StructureDescription: Mapped[Optional[str]] = mapped_column(String(50))

    functions: Mapped[List['Function']] = relationship(back_populates='structure', lazy='dynamic')

class Function(Base):
    __tablename__ = 'Functions'
    __table_args__ = {'schema': 'dbo'}

    FunctionId: Mapped[int] = mapped_column(Integer, primary_key=True)
    FunctionCode: Mapped[int] = mapped_column(Integer, nullable=False)
    FunctionDescription: Mapped[str] = mapped_column(String(50), nullable=False)
    DirectEmployee: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, server_default=text('0'))
    IsStructure: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    NoDayAnnouncementToQuit: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    StructureId: Mapped[Optional[int]] = mapped_column(ForeignKey('dbo.FunctionsStructure.StructureId'), nullable=True)
    TimeClockingProfessionID: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)

    structure: Mapped[Optional['FunctionsStructure']] = relationship(back_populates='functions', lazy='select')

class Employeer(Base):
    __tablename__ = 'Employeers'
    __table_args__ = {'schema': 'dbo'}

    EmployeerId: Mapped[int] = mapped_column(Integer, primary_key=True)
    EmployeerName: Mapped[Optional[str]] = mapped_column(String(100))
    EmployeerFiscalCode: Mapped[Optional[str]] = mapped_column(String(20))
    EmployeerRegCode: Mapped[Optional[str]] = mapped_column(String(20))
    PointOfWorkOfId: Mapped[Optional[int]] = mapped_column(ForeignKey('dbo.Employeers.EmployeerId'), nullable=True)
    DateIn: Mapped[Optional[datetime]] = mapped_column(DateTime, default=func.getdate(), server_default=func.getdate())
    DateOut: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    parent_employeer: Mapped[Optional['Employeer']] = relationship(back_populates='child_employeers', remote_side=[EmployeerId], lazy='select')
    child_employeers: Mapped[List['Employeer']] = relationship(back_populates='parent_employeer', lazy='dynamic')

class ContractType(Base):
    __tablename__ = 'ContractTypes'
    __table_args__ = {'schema': 'dbo'}

    ContractTypeId: Mapped[int] = mapped_column(Integer, primary_key=True)
    ContractType: Mapped[Optional[str]] = mapped_column(String(30))
    NoHours: Mapped[Optional[int]] = mapped_column(SmallInteger, default=8, server_default=text('8'))
    Partial: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, server_default=text('0'))
    ContractTypeRom: Mapped[Optional[str]] = mapped_column(String(50))
    TestPeriod: Mapped[Optional[int]] = mapped_column(SmallInteger, default=90, server_default=text('90'))
    Acronimo: Mapped[Optional[str]] = mapped_column(String(6))

class CodeCore(Base):
    __tablename__ = 'CodeCores'
    __table_args__ = {'schema': 'dbo'}

    CodeCoresId: Mapped[int] = mapped_column(Integer, primary_key=True)
    CoreCode: Mapped[Optional[str]] = mapped_column(String(15))
    CoreDescription: Mapped[Optional[str]] = mapped_column(String(200))
    DateIn: Mapped[Optional[datetime]] = mapped_column(DateTime, default=func.getdate(), server_default=func.getdate())
    DateOut: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
