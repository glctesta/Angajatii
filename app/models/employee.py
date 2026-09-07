from sqlalchemy import String, Integer, SmallInteger, Boolean, DateTime, Date, ForeignKey, Index, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from datetime import date, datetime
from .base import Base

class Employee(Base):
    __tablename__ = 'Employees'
    __table_args__ = (
        Index('UniCNP', 'EmployeeId', 'EmployeeName', 'EmployeeSurname', 'EmployeeNID', unique=True),
        {'schema': 'dbo'}
    )

    EmployeeId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    EmployeeNID: Mapped[str] = mapped_column(String(30), nullable=False)
    EmployeeName: Mapped[str] = mapped_column(String(50), nullable=False)
    EmployeeSurname: Mapped[str] = mapped_column(String(50), nullable=False)
    EmployeeOldSurName: Mapped[Optional[str]] = mapped_column(String(50))
    EmployeeBirthDate: Mapped[date] = mapped_column(Date, nullable=False)
    BirthCityId: Mapped[Optional[int]] = mapped_column(ForeignKey('Geo.Towns.TownId'))
    EmployeeSex: Mapped[Optional[str]] = mapped_column(String(1), default='M', server_default=text("'M'"))
    PicturePath: Mapped[Optional[str]] = mapped_column(String(200))
    EmployeePassword: Mapped[Optional[str]] = mapped_column(String(50))
    AccessId: Mapped[Optional[int]] = mapped_column(Integer)
    PasswordTrace: Mapped[Optional[str]] = mapped_column(String(30))
    DateIn: Mapped[Optional[datetime]] = mapped_column(DateTime, default=func.getdate(), server_default=func.getdate())
    NotValidForLegalDoc: Mapped[Optional[bool]] = mapped_column(Boolean)

    hire_history: Mapped[List['EmployeeHireHistory']] = relationship(back_populates='employee', lazy='dynamic')
    
    @property
    def full_name(self) -> str:
        return f"{self.EmployeeSurname} {self.EmployeeName}"
    
    @property
    def is_male(self) -> bool:
        return self.EmployeeSex == 'M'
        
    @property
    def is_female(self) -> bool:
        return self.EmployeeSex == 'F'

class EmployeeHireHistory(Base):
    __tablename__ = 'EmployeeHireHistory'
    __table_args__ = {'schema': 'dbo'}

    EmployeeHireHistoryId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    EmployeeId: Mapped[int] = mapped_column(ForeignKey('dbo.Employees.EmployeeId'), nullable=False)
    EmployeerId: Mapped[int] = mapped_column(ForeignKey('dbo.Employeers.EmployeerId'), nullable=False)
    IdRegistroOffer: Mapped[Optional[int]] = mapped_column(Integer)
    IdRegistroCm: Mapped[Optional[int]] = mapped_column(Integer)
    ContractTypeId: Mapped[Optional[int]] = mapped_column(ForeignKey('dbo.ContractTypes.ContractTypeId'))
    HireDate: Mapped[date] = mapped_column(Date, nullable=False)
    StartWorkDate: Mapped[Optional[date]] = mapped_column(Date)
    EndWorkDate: Mapped[Optional[date]] = mapped_column(Date)
    DateSys: Mapped[Optional[datetime]] = mapped_column(DateTime, default=func.getdate(), server_default=func.getdate())
    HourPerDay: Mapped[Optional[int]] = mapped_column(SmallInteger)
    HolidayPerYear: Mapped[Optional[int]] = mapped_column(SmallInteger, default=21, server_default=text('21'))
    CoreHiringCode: Mapped[Optional[str]] = mapped_column(String(15))
    HiringSalary: Mapped[Optional[int]] = mapped_column(Integer)
    NoWorkContract: Mapped[Optional[str]] = mapped_column(String(50))
    DateOut: Mapped[Optional[datetime]] = mapped_column(DateTime)
    ChiusoPerModifica: Mapped[Optional[bool]] = mapped_column(Boolean)
    ModificatoDa: Mapped[Optional[str]] = mapped_column(String(30))
    AccessID: Mapped[Optional[int]] = mapped_column(Integer)
    TestPeriod: Mapped[Optional[int]] = mapped_column(SmallInteger, default=90, server_default=text('90'))
    NoNotaLichidare: Mapped[Optional[str]] = mapped_column(String(25))
    DataNotaLichidare: Mapped[Optional[date]] = mapped_column(Date)
    RichiestaLicenziamento: Mapped[Optional[str]] = mapped_column(String(500))
    DataRichiestaLicenziamento: Mapped[Optional[date]] = mapped_column(Date)
    ArtLegaleLicenziamento: Mapped[Optional[str]] = mapped_column(String(500))
    IdRichiestaLicenziamento: Mapped[Optional[int]] = mapped_column(Integer)
    ConsensoInformato: Mapped[Optional[bool]] = mapped_column(Boolean)
    CodeCoresId: Mapped[Optional[int]] = mapped_column(ForeignKey('dbo.CodeCores.CodeCoresId'))
    SedeLavoroId: Mapped[Optional[int]] = mapped_column(ForeignKey('dbo.Employeers.EmployeerId'))
    ArticoloLegaleId: Mapped[Optional[int]] = mapped_column(Integer)
    NotaDeLichidareId: Mapped[Optional[int]] = mapped_column(Integer)
    NrDeciziaIncetareId: Mapped[Optional[int]] = mapped_column(Integer)
    RepartitionDecizionId: Mapped[Optional[int]] = mapped_column(Integer)
    RecordedIntoRevisal: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, server_default=text('0'))
    JustForReport: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, server_default=text('0'))
    EndWorkDateContract: Mapped[Optional[date]] = mapped_column(Date)

    employee: Mapped['Employee'] = relationship(back_populates='hire_history', lazy='select')
    cdc_stories: Mapped[List['EmployeeCdcStory']] = relationship(back_populates='hire_history', lazy='dynamic')
    
    @property
    def is_active(self) -> bool:
        return self.EndWorkDate is None

class EmployeeCdcStory(Base):
    __tablename__ = 'EmployeeCdcStories'
    __table_args__ = {'schema': 'dbo'}

    EmployeeCdcStoryId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    EmployeeHireHistoryId: Mapped[Optional[int]] = mapped_column(ForeignKey('dbo.EmployeeHireHistory.EmployeeHireHistoryId'))
    SubCdcId: Mapped[int] = mapped_column(ForeignKey('dbo.CdcSub.SubCdcId'), nullable=False)
    FunctionId: Mapped[int] = mapped_column(ForeignKey('dbo.Functions.FunctionId'), nullable=False)
    DateIn: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.getdate(), server_default=func.getdate())
    DateOut: Mapped[Optional[datetime]] = mapped_column(DateTime)

    hire_history: Mapped[Optional['EmployeeHireHistory']] = relationship(back_populates='cdc_stories', lazy='select')
    
    @property
    def is_current(self) -> bool:
        return self.DateOut is None
