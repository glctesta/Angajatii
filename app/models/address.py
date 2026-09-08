"""
Address, Family, Document models.
Aligned with source Employee database structure.
"""
from sqlalchemy import String, Integer, SmallInteger, Boolean, DateTime, Date, ForeignKey, func, text
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from datetime import date, datetime
from .base import Base


class EmployeeAddress(Base):
    __tablename__ = 'EmployeeAddress'
    __table_args__ = {'schema': 'dbo'}

    AddressId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    EmployeeId: Mapped[int] = mapped_column(ForeignKey('dbo.Employees.EmployeeId'), nullable=False)
    TownAddressId: Mapped[Optional[int]] = mapped_column(ForeignKey('Geo.Towns.TownId'))
    Street: Mapped[Optional[str]] = mapped_column(String(50))
    Street2: Mapped[Optional[str]] = mapped_column(String(100))
    NumeroCivico: Mapped[Optional[str]] = mapped_column(String(10))
    Bloc: Mapped[Optional[str]] = mapped_column(String(50))
    Scala: Mapped[Optional[str]] = mapped_column(String(10))
    Piano: Mapped[Optional[str]] = mapped_column(String(5))
    Apartment: Mapped[Optional[str]] = mapped_column(String(10))
    TelephoneNo1: Mapped[Optional[str]] = mapped_column(String(50))
    TelephoneNo2: Mapped[Optional[str]] = mapped_column(String(50))
    Email: Mapped[Optional[str]] = mapped_column(String(100))
    WorkEmail: Mapped[Optional[str]] = mapped_column(String(150))
    Twitter: Mapped[Optional[str]] = mapped_column(String(50))
    HasWhatsApp: Mapped[Optional[bool]] = mapped_column(Boolean)
    HasEmail: Mapped[Optional[bool]] = mapped_column(Boolean)
    DateIn: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.getdate(), server_default=func.getdate())
    DateOut: Mapped[Optional[datetime]] = mapped_column(DateTime)


class RelativeType(Base):
    __tablename__ = 'RelativeTypes'
    __table_args__ = {'schema': 'dbo'}

    FamilyRelativeId: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    RelationType: Mapped[Optional[str]] = mapped_column(String(30))
    MajorityLimited: Mapped[Optional[bool]] = mapped_column(Boolean)
    DateOut: Mapped[Optional[date]] = mapped_column(Date)


class EmployeeChild(Base):
    __tablename__ = 'EmployeeChildren'
    __table_args__ = {'schema': 'dbo'}

    EmployeeFamilyId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    FamilyRelativeId: Mapped[Optional[int]] = mapped_column(SmallInteger, ForeignKey('dbo.RelativeTypes.FamilyRelativeId'))
    ChildName: Mapped[str] = mapped_column(String(100), nullable=False)
    ChildBirthDate: Mapped[date] = mapped_column(Date, nullable=False)
    CNPChild: Mapped[str] = mapped_column(String(16), nullable=False)
    EmployeeId: Mapped[int] = mapped_column(ForeignKey('dbo.Employees.EmployeeId'), nullable=False)
    DateIn: Mapped[Optional[date]] = mapped_column(Date)
    DateOut: Mapped[Optional[datetime]] = mapped_column(DateTime)


class DocumentType(Base):
    __tablename__ = 'DocumentTypes'
    __table_args__ = {'schema': 'dbo'}

    DocumentTypeId: Mapped[int] = mapped_column(Integer, primary_key=True)
    DocumentName: Mapped[Optional[str]] = mapped_column(String(15))
    Acronim: Mapped[Optional[str]] = mapped_column(String(5))
    DocNameRo: Mapped[Optional[str]] = mapped_column(String(30))
    AcronimRo: Mapped[Optional[str]] = mapped_column(String(5))
    IsLegal: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, server_default=text('0'))
    IsReadle: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, server_default=text('0'))


class EmployeeDocument(Base):
    __tablename__ = 'EmployeeDocuments'
    __table_args__ = {'schema': 'dbo'}

    IdDocEmplolyee: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    DocID: Mapped[int] = mapped_column(Integer, nullable=False)
    EmployeeID: Mapped[int] = mapped_column(Integer, nullable=False)
    EmployeeId: Mapped[Optional[int]] = mapped_column(ForeignKey('dbo.Employees.EmployeeId'))
    EmployeeHireHistoryId: Mapped[Optional[int]] = mapped_column(ForeignKey('dbo.EmployeeHireHistory.EmployeeHireHistoryId'))
    SkillMatrixId: Mapped[Optional[int]] = mapped_column(Integer)
    FileName: Mapped[str] = mapped_column(String(255), nullable=False)
    DocTypeId: Mapped[int] = mapped_column(Integer, ForeignKey('dbo.DocumentTypes.DocumentTypeId'), nullable=False)
    DocSerie: Mapped[Optional[str]] = mapped_column(String(5))
    FileType: Mapped[str] = mapped_column(String(10), nullable=False)
    FileSize: Mapped[Optional[int]] = mapped_column(Integer)
    DocNumber: Mapped[Optional[str]] = mapped_column(String(15))
    IussedDateDoc: Mapped[Optional[date]] = mapped_column(Date)
    DocIsussedBy: Mapped[Optional[str]] = mapped_column(String(50))
    ExpirationDateDoc: Mapped[Optional[date]] = mapped_column(Date)
    Notes: Mapped[Optional[str]] = mapped_column(String(300))
    DateIn: Mapped[Optional[datetime]] = mapped_column(DateTime, default=func.getdate(), server_default=func.getdate())
    DateOut: Mapped[Optional[datetime]] = mapped_column(DateTime)
    IdTown: Mapped[Optional[int]] = mapped_column(Integer)
