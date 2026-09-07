from sqlalchemy import String, Integer, Boolean, DateTime, Date, ForeignKey, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from datetime import date, datetime
from .base import Base

class EmployeeAddress(Base):
    __tablename__ = 'EmployeeAddress'
    __table_args__ = {'schema': 'dbo'}

    EmployeeAddressId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    EmployeeId: Mapped[int] = mapped_column(ForeignKey('dbo.Employees.EmployeeId'), nullable=False)
    TownAddressId: Mapped[Optional[int]] = mapped_column(ForeignKey('Geo.Towns.TownId'))
    Street: Mapped[Optional[str]] = mapped_column(String(100))
    Street2: Mapped[Optional[str]] = mapped_column(String(100))
    Bloc: Mapped[Optional[str]] = mapped_column(String(10))
    Scala: Mapped[Optional[str]] = mapped_column(String(5))
    Piano: Mapped[Optional[str]] = mapped_column(String(5))
    NumeroCivico: Mapped[Optional[str]] = mapped_column(String(10))
    WorkEmail: Mapped[Optional[str]] = mapped_column(String(100))
    PersonalEmail: Mapped[Optional[str]] = mapped_column(String(100))
    Phone: Mapped[Optional[str]] = mapped_column(String(20))
    Phone2: Mapped[Optional[str]] = mapped_column(String(20))
    DateIn: Mapped[Optional[datetime]] = mapped_column(DateTime, default=func.getdate(), server_default=func.getdate())
    DateOut: Mapped[Optional[datetime]] = mapped_column(DateTime)

class RelativeType(Base):
    __tablename__ = 'RelativeTypes'
    __table_args__ = {'schema': 'dbo'}

    FamilyRelativeId: Mapped[int] = mapped_column(Integer, primary_key=True)
    RelativeDescription: Mapped[Optional[str]] = mapped_column(String(50))

class EmployeeChild(Base):
    __tablename__ = 'EmployeeChildren'
    __table_args__ = {'schema': 'dbo'}

    EmployeeChildrenId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    EmployeeId: Mapped[int] = mapped_column(ForeignKey('dbo.Employees.EmployeeId'), nullable=False)
    ChildName: Mapped[Optional[str]] = mapped_column(String(50))
    ChildSurname: Mapped[Optional[str]] = mapped_column(String(50))
    ChildBirthDate: Mapped[Optional[date]] = mapped_column(Date)
    ChildCNP: Mapped[Optional[str]] = mapped_column(String(13))
    FamilyRelativeId: Mapped[Optional[int]] = mapped_column(ForeignKey('dbo.RelativeTypes.FamilyRelativeId'))
    DateIn: Mapped[Optional[datetime]] = mapped_column(DateTime, default=func.getdate(), server_default=func.getdate())
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

    EmployeeDocumentId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    EmployeeId: Mapped[int] = mapped_column(ForeignKey('dbo.Employees.EmployeeId'), nullable=False)
    EmployeeHireHistoryId: Mapped[Optional[int]] = mapped_column(ForeignKey('dbo.EmployeeHireHistory.EmployeeHireHistoryId'))
    DocTypeId: Mapped[Optional[int]] = mapped_column(ForeignKey('dbo.DocumentTypes.DocumentTypeId'))
    DocSerie: Mapped[Optional[str]] = mapped_column(String(10))
    DocNumber: Mapped[Optional[str]] = mapped_column(String(20))
    DocIsussedBy: Mapped[Optional[str]] = mapped_column(String(100))
    IussedDateDoc: Mapped[Optional[date]] = mapped_column(Date)
    DocExpireDate: Mapped[Optional[date]] = mapped_column(Date)
    DateIn: Mapped[Optional[datetime]] = mapped_column(DateTime, default=func.getdate(), server_default=func.getdate())
    DateOut: Mapped[Optional[datetime]] = mapped_column(DateTime)
