import pyodbc
import os
import sys
from datetime import datetime
from app.extensions import db
from app.models import *

class ImportService:
    """Service for importing data from various sources into the Employees database."""
    
    def __init__(self):
        self.stats = {'imported': 0, 'skipped': 0, 'errors': 0, 'details': []}
    
    def import_from_employee_db(self, progress_callback=None):
        """Full import from the existing Employee database.
        Import order matters due to FK dependencies.
        """
        source_conn = self._get_source_connection('Employee')
        cursor = source_conn.cursor()
        
        steps = [
            ('Geografia - Continenti', self._import_continents),
            ('Geografia - Nazioni', self._import_nations),
            ('Geografia - Province', self._import_counties),
            ('Geografia - Citta', self._import_towns),
            ('Centri di Costo', self._import_cost_centers),
            ('Sotto-Centri di Costo', self._import_cdc_sub),
            ('Struttura Funzioni', self._import_functions_structure),
            ('Funzioni', self._import_functions),
            ('Tipi Contratto', self._import_contract_types),
            ('Entita Produttive', self._import_employeers),
            ('Codici Core', self._import_code_cores),
            ('Turni', self._import_shifts),
            ('Orari Turni', self._import_shift_timetable),
            ('Tipi Parentela', self._import_relative_types),
            ('Tipi Documento', self._import_document_types),
            ('Dipendenti', self._import_employees),
            ('Badge', self._import_badges),
            ('Storico Assunzioni', self._import_hire_history),
            ('Storico CdC', self._import_cdc_stories),
            ('Storico Badge', self._import_badge_history),
            ('Indirizzi', self._import_addresses),
            ('Familiari', self._import_children),
            ('Documenti', self._import_documents),
        ]
        
        total = len(steps)
        for i, (name, func) in enumerate(steps, 1):
            try:
                if progress_callback:
                    progress_callback(i, total, name)
                count = func(cursor)
                self.stats['details'].append({'step': name, 'imported': count, 'status': 'ok'})
                self.stats['imported'] += count
            except Exception as e:
                self.stats['errors'] += 1
                self.stats['details'].append({'step': name, 'imported': 0, 'status': 'error', 'error': str(e)})
        
        source_conn.close()
        return self.stats
    
    def _get_source_connection(self, database_name):
        """Get pyodbc connection to source database using encrypted credentials."""
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if root_dir not in sys.path:
            sys.path.insert(0, root_dir)
        from config_manager import ConfigManager
        
        manager = ConfigManager(
            key_file=os.path.join(root_dir, 'encryption_key.key'),
            config_file=os.path.join(root_dir, 'db_config.enc')
        )
        config = manager.load_config()
        
        drivers = ['ODBC Driver 18 for SQL Server', 'ODBC Driver 17 for SQL Server', 'SQL Server']
        driver = None
        for d in drivers:
            if d in pyodbc.drivers():
                driver = d
                break
        
        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={config['server']};"
            f"DATABASE={database_name};"
            f"UID={config['username']};"
            f"PWD={config['password']};"
            "TrustServerCertificate=yes;Encrypt=yes;"
        )
        return pyodbc.connect(conn_str)
    
    def _import_continents(self, cursor):
        cursor.execute('SELECT ContinentId, ContinentName FROM Geo.Continents')
        count = 0
        for row in cursor.fetchall():
            existing = db.session.query(Continent).filter_by(ContinentId=row.ContinentId).first()
            if not existing:
                db.session.add(Continent(ContinentId=row.ContinentId, ContinentName=row.ContinentName))
                count += 1
        db.session.commit()
        return count
    
    def _import_nations(self, cursor):
        cursor.execute('SELECT NationId, NationName, ContinentId, UE, IsoCode FROM Geo.Nations')
        count = 0
        for row in cursor.fetchall():
            existing = db.session.query(Nation).filter_by(NationId=row.NationId).first()
            if not existing:
                db.session.add(Nation(NationId=row.NationId, NationName=row.NationName, ContinentId=row.ContinentId, UE=row.UE, IsoCode=row.IsoCode))
                count += 1
        db.session.commit()
        return count

    def _import_counties(self, cursor):
        cursor.execute('SELECT CountyId, CountyName, NationId, ProvinceCode, StartDate, EndDate FROM Geo.Counties')
        count = 0
        for row in cursor.fetchall():
            existing = db.session.query(County).filter_by(CountyId=row.CountyId).first()
            if not existing:
                db.session.add(County(CountyId=row.CountyId, CountyName=row.CountyName, NationId=row.NationId, ProvinceCode=row.ProvinceCode, StartDate=row.StartDate, EndDate=row.EndDate))
                count += 1
        db.session.commit()
        return count
        
    def _import_towns(self, cursor):
        cursor.execute('SELECT TownId, TownName, CountyId, StartDate, EndDate, IsEstonia, CadastralCode FROM Geo.Towns')
        count = 0
        for row in cursor.fetchall():
            existing = db.session.query(Town).filter_by(TownId=row.TownId).first()
            if not existing:
                db.session.add(Town(TownId=row.TownId, TownName=row.TownName, CountyId=row.CountyId, StartDate=row.StartDate, EndDate=row.EndDate, IsEstonia=row.IsEstonia, CadastralCode=row.CadastralCode))
                count += 1
        db.session.commit()
        return count

    def _import_cost_centers(self, cursor):
        cursor.execute('SELECT CostCenterId, CostCenterName, CostCenterCode FROM dbo.CostCenters')
        count = 0
        for row in cursor.fetchall():
            existing = db.session.query(CostCenter).filter_by(CostCenterId=row.CostCenterId).first()
            if not existing:
                db.session.add(CostCenter(CostCenterId=row.CostCenterId, CostCenterName=row.CostCenterName, CostCenterCode=row.CostCenterCode))
                count += 1
        db.session.commit()
        return count

    def _import_cdc_sub(self, cursor):
        cursor.execute('SELECT CdcSubId, CostCenterId, CdcSubName FROM dbo.CdcSub')
        count = 0
        for row in cursor.fetchall():
            existing = db.session.query(CdcSub).filter_by(CdcSubId=row.CdcSubId).first()
            if not existing:
                db.session.add(CdcSub(CdcSubId=row.CdcSubId, CostCenterId=row.CostCenterId, CdcSubName=row.CdcSubName))
                count += 1
        db.session.commit()
        return count

    def _import_functions_structure(self, cursor):
        cursor.execute('SELECT StructureId, StructureName FROM dbo.FunctionsStructure')
        count = 0
        for row in cursor.fetchall():
            existing = db.session.query(FunctionsStructure).filter_by(StructureId=row.StructureId).first()
            if not existing:
                db.session.add(FunctionsStructure(StructureId=row.StructureId, StructureName=row.StructureName))
                count += 1
        db.session.commit()
        return count

    def _import_functions(self, cursor):
        cursor.execute('SELECT FunctionId, StructureId, FunctionName FROM dbo.Functions')
        count = 0
        for row in cursor.fetchall():
            existing = db.session.query(Function).filter_by(FunctionId=row.FunctionId).first()
            if not existing:
                db.session.add(Function(FunctionId=row.FunctionId, StructureId=row.StructureId, FunctionName=row.FunctionName))
                count += 1
        db.session.commit()
        return count

    def _import_contract_types(self, cursor):
        cursor.execute('SELECT ContractTypeId, ContractTypeName FROM dbo.ContractTypes')
        count = 0
        for row in cursor.fetchall():
            existing = db.session.query(ContractType).filter_by(ContractTypeId=row.ContractTypeId).first()
            if not existing:
                db.session.add(ContractType(ContractTypeId=row.ContractTypeId, ContractTypeName=row.ContractTypeName))
                count += 1
        db.session.commit()
        return count

    def _import_employeers(self, cursor):
        cursor.execute('SELECT EmployeerId, EmployeerName, EmployeerCode FROM dbo.Employeers')
        count = 0
        for row in cursor.fetchall():
            existing = db.session.query(Employeer).filter_by(EmployeerId=row.EmployeerId).first()
            if not existing:
                db.session.add(Employeer(EmployeerId=row.EmployeerId, EmployeerName=row.EmployeerName, EmployeerCode=row.EmployeerCode))
                count += 1
        db.session.commit()
        return count

    def _import_code_cores(self, cursor):
        # We need to query CodeCore from source if it exists. Some schemas may not have it or have it differently named. Let's assume CodeCores
        try:
            cursor.execute('SELECT CodeId, CodeName FROM dbo.CodeCores')
        except pyodbc.ProgrammingError:
            return 0
        count = 0
        for row in cursor.fetchall():
            existing = db.session.query(CodeCore).filter_by(CodeId=row.CodeId).first()
            if not existing:
                db.session.add(CodeCore(CodeId=row.CodeId, CodeName=row.CodeName))
                count += 1
        db.session.commit()
        return count

    def _import_shifts(self, cursor):
        try:
            cursor.execute('SELECT ShiftId, ShiftName, ShiftDescription FROM dbo.Shifts')
        except pyodbc.ProgrammingError:
            return 0
        count = 0
        for row in cursor.fetchall():
            existing = db.session.query(Shift).filter_by(ShiftId=row.ShiftId).first()
            if not existing:
                db.session.add(Shift(ShiftId=row.ShiftId, ShiftName=row.ShiftName, ShiftDescription=row.ShiftDescription))
                count += 1
        db.session.commit()
        return count

    def _import_shift_timetable(self, cursor):
        try:
            cursor.execute('SELECT ShiftTimeTableId, ShiftId, StartTime, EndTime, DayOfWeek FROM dbo.ShiftTimeTable')
        except pyodbc.ProgrammingError:
            return 0
        count = 0
        for row in cursor.fetchall():
            existing = db.session.query(ShiftTimeTable).filter_by(ShiftTimeTableId=row.ShiftTimeTableId).first()
            if not existing:
                db.session.add(ShiftTimeTable(ShiftTimeTableId=row.ShiftTimeTableId, ShiftId=row.ShiftId, StartTime=row.StartTime, EndTime=row.EndTime, DayOfWeek=row.DayOfWeek))
                count += 1
        db.session.commit()
        return count

    def _import_relative_types(self, cursor):
        try:
            cursor.execute('SELECT RelativeTypeId, RelativeTypeName FROM dbo.RelativeTypes')
        except pyodbc.ProgrammingError:
            return 0
        count = 0
        for row in cursor.fetchall():
            existing = db.session.query(RelativeType).filter_by(RelativeTypeId=row.RelativeTypeId).first()
            if not existing:
                db.session.add(RelativeType(RelativeTypeId=row.RelativeTypeId, RelativeTypeName=row.RelativeTypeName))
                count += 1
        db.session.commit()
        return count

    def _import_document_types(self, cursor):
        try:
            cursor.execute('SELECT DocumentTypeId, DocumentTypeName FROM dbo.DocumentTypes')
        except pyodbc.ProgrammingError:
            return 0
        count = 0
        for row in cursor.fetchall():
            existing = db.session.query(DocumentType).filter_by(DocumentTypeId=row.DocumentTypeId).first()
            if not existing:
                db.session.add(DocumentType(DocumentTypeId=row.DocumentTypeId, DocumentTypeName=row.DocumentTypeName))
                count += 1
        db.session.commit()
        return count

    def _import_employees(self, cursor):
        cursor.execute('''
            SELECT EmployeeId, EmployeeNID, EmployeeName, EmployeeSurname, EmployeeOldSurName, 
                   EmployeeBirthDate, BirthCityId, EmployeeSex, PicturePath, EmployeePassword, 
                   AccessId, PasswordTrace, DateIn, NotValidForLegalDoc 
            FROM dbo.Employees
        ''')
        count = 0
        for row in cursor.fetchall():
            existing = db.session.query(Employee).filter_by(EmployeeId=row.EmployeeId).first()
            if not existing:
                emp = Employee(
                    EmployeeId=row.EmployeeId,
                    EmployeeNID=row.EmployeeNID,
                    EmployeeName=row.EmployeeName,
                    EmployeeSurname=row.EmployeeSurname,
                    EmployeeOldSurName=row.EmployeeOldSurName,
                    EmployeeBirthDate=row.EmployeeBirthDate,
                    BirthCityId=row.BirthCityId,
                    EmployeeSex=row.EmployeeSex,
                    PicturePath=row.PicturePath,
                    EmployeePassword=row.EmployeePassword,
                    AccessId=row.AccessId,
                    PasswordTrace=row.PasswordTrace,
                    DateIn=row.DateIn,
                    NotValidForLegalDoc=row.NotValidForLegalDoc
                )
                db.session.add(emp)
                count += 1
        db.session.commit()
        return count

    def _import_badges(self, cursor):
        try:
            cursor.execute('SELECT BadgeId, BadgeCode, BadgeStatus, IssueDate, ExpiryDate FROM dbo.Badges')
        except pyodbc.ProgrammingError:
            return 0
        count = 0
        for row in cursor.fetchall():
            existing = db.session.query(Badge).filter_by(BadgeId=row.BadgeId).first()
            if not existing:
                db.session.add(Badge(BadgeId=row.BadgeId, BadgeCode=row.BadgeCode, BadgeStatus=row.BadgeStatus, IssueDate=row.IssueDate, ExpiryDate=row.ExpiryDate))
                count += 1
        db.session.commit()
        return count

    def _import_hire_history(self, cursor):
        cursor.execute('''
            SELECT EmployeeHireHistoryId, EmployeeId, EmployeerId, ContractTypeId, HireDate, 
                   StartWorkDate, EndWorkDate, DateSys, HourPerDay, HolidayPerYear, 
                   CoreHiringCode, HiringSalary, NoWorkContract 
            FROM dbo.EmployeeHireHistory
        ''')
        count = 0
        for row in cursor.fetchall():
            existing = db.session.query(EmployeeHireHistory).filter_by(EmployeeHireHistoryId=row.EmployeeHireHistoryId).first()
            if not existing:
                db.session.add(EmployeeHireHistory(
                    EmployeeHireHistoryId=row.EmployeeHireHistoryId,
                    EmployeeId=row.EmployeeId,
                    EmployeerId=row.EmployeerId,
                    ContractTypeId=row.ContractTypeId,
                    HireDate=row.HireDate,
                    StartWorkDate=row.StartWorkDate,
                    EndWorkDate=row.EndWorkDate,
                    DateSys=row.DateSys,
                    HourPerDay=row.HourPerDay,
                    HolidayPerYear=row.HolidayPerYear,
                    CoreHiringCode=row.CoreHiringCode,
                    HiringSalary=row.HiringSalary,
                    NoWorkContract=row.NoWorkContract
                ))
                count += 1
        db.session.commit()
        return count

    def _import_cdc_stories(self, cursor):
        cursor.execute('''
            SELECT StoryId, EmployeeId, CdcSubId, StartDate, EndDate, FunctionId, ShiftId 
            FROM dbo.EmployeeCdcStories
        ''')
        count = 0
        for row in cursor.fetchall():
            existing = db.session.query(EmployeeCdcStory).filter_by(StoryId=row.StoryId).first()
            if not existing:
                db.session.add(EmployeeCdcStory(
                    StoryId=row.StoryId,
                    EmployeeId=row.EmployeeId,
                    CdcSubId=row.CdcSubId,
                    StartDate=row.StartDate,
                    EndDate=row.EndDate,
                    FunctionId=row.FunctionId,
                    ShiftId=row.ShiftId
                ))
                count += 1
        db.session.commit()
        return count

    def _import_badge_history(self, cursor):
        try:
            cursor.execute('SELECT HistoryId, EmployeeId, BadgeId, AssignmentDate, ReturnDate, Status FROM dbo.EmployeeBadgeHistory')
        except pyodbc.ProgrammingError:
            return 0
        count = 0
        for row in cursor.fetchall():
            existing = db.session.query(EmployeeBadgeHistory).filter_by(HistoryId=row.HistoryId).first()
            if not existing:
                db.session.add(EmployeeBadgeHistory(
                    HistoryId=row.HistoryId,
                    EmployeeId=row.EmployeeId,
                    BadgeId=row.BadgeId,
                    AssignmentDate=row.AssignmentDate,
                    ReturnDate=row.ReturnDate,
                    Status=row.Status
                ))
                count += 1
        db.session.commit()
        return count

    def _import_addresses(self, cursor):
        try:
            cursor.execute('''
                SELECT AddressId, EmployeeId, AddressType, Street, CityId, ZipCode, 
                       ContactPhone, ContactEmail, StartDate, EndDate 
                FROM dbo.EmployeeAddress
            ''')
        except pyodbc.ProgrammingError:
            return 0
        count = 0
        for row in cursor.fetchall():
            existing = db.session.query(EmployeeAddress).filter_by(AddressId=row.AddressId).first()
            if not existing:
                db.session.add(EmployeeAddress(
                    AddressId=row.AddressId,
                    EmployeeId=row.EmployeeId,
                    AddressType=row.AddressType,
                    Street=row.Street,
                    CityId=row.CityId,
                    ZipCode=row.ZipCode,
                    ContactPhone=row.ContactPhone,
                    ContactEmail=row.ContactEmail,
                    StartDate=row.StartDate,
                    EndDate=row.EndDate
                ))
                count += 1
        db.session.commit()
        return count

    def _import_children(self, cursor):
        try:
            cursor.execute('SELECT ChildId, EmployeeId, RelativeTypeId, FirstName, LastName, BirthDate FROM dbo.EmployeeChildren')
        except pyodbc.ProgrammingError:
            return 0
        count = 0
        for row in cursor.fetchall():
            existing = db.session.query(EmployeeChild).filter_by(ChildId=row.ChildId).first()
            if not existing:
                db.session.add(EmployeeChild(
                    ChildId=row.ChildId,
                    EmployeeId=row.EmployeeId,
                    RelativeTypeId=row.RelativeTypeId,
                    FirstName=row.FirstName,
                    LastName=row.LastName,
                    BirthDate=row.BirthDate
                ))
                count += 1
        db.session.commit()
        return count

    def _import_documents(self, cursor):
        try:
            cursor.execute('''
                SELECT DocumentId, EmployeeId, DocumentTypeId, DocumentNumber, 
                       IssueDate, ExpiryDate, IssuingAuthority, DocumentPath 
                FROM dbo.EmployeeDocuments
            ''')
        except pyodbc.ProgrammingError:
            return 0
        count = 0
        for row in cursor.fetchall():
            existing = db.session.query(EmployeeDocument).filter_by(DocumentId=row.DocumentId).first()
            if not existing:
                db.session.add(EmployeeDocument(
                    DocumentId=row.DocumentId,
                    EmployeeId=row.EmployeeId,
                    DocumentTypeId=row.DocumentTypeId,
                    DocumentNumber=row.DocumentNumber,
                    IssueDate=row.IssueDate,
                    ExpiryDate=row.ExpiryDate,
                    IssuingAuthority=row.IssuingAuthority,
                    DocumentPath=row.DocumentPath
                ))
                count += 1
        db.session.commit()
        return count
