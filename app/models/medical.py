"""
Medical models.
MedicalCenter = Centri medici convenzionati
MedicalDoctor = Medici del centro
MedicalVisitSchedule = Programmazione visite mediche candidati
"""
from sqlalchemy import String, Integer, Boolean, DateTime, Date, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from datetime import datetime, date
from .base import Base


class MedicalCenter(Base):
    __tablename__ = 'MedicalCenters'
    __table_args__ = {'schema': 'dbo'}

    MedicalCenterId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    CenterName: Mapped[str] = mapped_column(String(100), nullable=False)
    Address: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    TownId: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('Geo.Towns.TownId'), nullable=True)
    Phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    Email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ContactPerson: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ContractStartDate: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    ContractEndDate: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    IsActive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    Notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    DateIn: Mapped[Optional[datetime]] = mapped_column(DateTime, default=func.getdate(), server_default=func.getdate())

    doctors: Mapped[List['MedicalDoctor']] = relationship(back_populates='center', lazy='select')


class MedicalDoctor(Base):
    __tablename__ = 'MedicalDoctors'
    __table_args__ = {'schema': 'dbo'}

    DoctorId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    MedicalCenterId: Mapped[int] = mapped_column(Integer, ForeignKey('dbo.MedicalCenters.MedicalCenterId'), nullable=False)
    DoctorName: Mapped[str] = mapped_column(String(50), nullable=False)
    DoctorSurname: Mapped[str] = mapped_column(String(50), nullable=False)
    Specialization: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    Phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    Email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    IsActive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    DateIn: Mapped[Optional[datetime]] = mapped_column(DateTime, default=func.getdate(), server_default=func.getdate())

    center: Mapped['MedicalCenter'] = relationship(back_populates='doctors', lazy='select')
    visits: Mapped[List['MedicalVisitSchedule']] = relationship(back_populates='doctor', lazy='dynamic')

    @property
    def full_name(self) -> str:
        return f"Dr. {self.DoctorSurname} {self.DoctorName}"


class MedicalVisitSchedule(Base):
    __tablename__ = 'MedicalVisitSchedules'
    __table_args__ = {'schema': 'dbo'}

    VisitId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    EmployeeId: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('dbo.Employees.EmployeeId'), nullable=True)
    CandidateName: Mapped[str] = mapped_column(String(50), nullable=False)
    CandidateSurname: Mapped[str] = mapped_column(String(50), nullable=False)
    CandidateCNP: Mapped[Optional[str]] = mapped_column(String(13), nullable=True)
    MedicalCenterId: Mapped[int] = mapped_column(Integer, ForeignKey('dbo.MedicalCenters.MedicalCenterId'), nullable=False)
    DoctorId: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('dbo.MedicalDoctors.DoctorId'), nullable=True)
    ScheduledDate: Mapped[date] = mapped_column(Date, nullable=False)
    FunctionId: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('dbo.Functions.FunctionId'), nullable=True)
    CanDriveVehicles: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    Status: Mapped[str] = mapped_column(String(20), default='scheduled', nullable=False)  # scheduled, completed, cancelled
    Result: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # fit, unfit, conditional
    Notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    CreatedBy: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('app.Users.UserId'), nullable=True)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, default=func.getdate(), server_default=func.getdate())

    center: Mapped['MedicalCenter'] = relationship(lazy='select')
    doctor: Mapped[Optional['MedicalDoctor']] = relationship(back_populates='visits', lazy='select')
