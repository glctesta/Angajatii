"""
HiringService — orchestrates the complete hiring process.
"""
import os
import string
import secrets
from datetime import datetime, date
from typing import Optional
from app.extensions import db
from app.models import (
    Employee, EmployeeHireHistory, EmployeeCdcStory,
    EmployeeAddress, EmployeeChild, EmployeeDocument,
    Registry, RegistryType, Employeer,
    EmployeeDisciplinaryHistory
)
from app.models.auth import User, Role
from app.models.settings import AppSetting
from app.services.cnp_validator import validate_cnp


class HiringService:
    """Service to handle all steps of the hiring process."""

    @staticmethod
    def check_existing_employee(cnp: str) -> dict:
        """Check if an employee with this CNP already exists.
        Returns dict with employee info, contracts, and disciplinary count.
        """
        result = {'exists': False}
        employee = db.session.query(Employee).filter_by(EmployeeNID=cnp).first()
        if not employee:
            return result

        result['exists'] = True
        result['employee'] = employee

        # Get hire history
        contracts = db.session.query(
            EmployeeHireHistory, Employeer
        ).join(
            Employeer, EmployeeHireHistory.EmployeerId == Employeer.EmployeerId
        ).filter(
            EmployeeHireHistory.EmployeeId == employee.EmployeeId
        ).order_by(EmployeeHireHistory.HireDate.desc()).all()

        result['contracts'] = contracts

        # Disciplinary count
        disc_count = db.session.query(EmployeeDisciplinaryHistory).join(
            EmployeeHireHistory,
            EmployeeDisciplinaryHistory.EmployeeHireHistoryId == EmployeeHireHistory.EmployeeHireHistoryId
        ).filter(
            EmployeeHireHistory.EmployeeId == employee.EmployeeId
        ).count()
        result['disciplinary_count'] = disc_count

        return result

    @staticmethod
    def generate_contract_number(employeer_id: int, registry_type_id: int, doc_date: date, username: str) -> tuple:
        """Generate next progressive contract number.
        Returns (counter_number, doc_name, registry_id).
        """
        # Get max counter for this registry type and company
        max_counter = db.session.query(
            db.func.max(Registry.CounterPerDocType)
        ).filter(
            Registry.RegistryTypeId == registry_type_id,
            Registry.EmployeerId == employeer_id,
            Registry.IsDeleted == False
        ).scalar() or 0

        # Check start number from settings
        start_num = int(AppSetting.get_value('CONTRACT_NUMBER_START', '1'))
        next_counter = max(max_counter + 1, start_num)

        # DocName = nnnn/gg-mm-yyyy
        doc_name = f"{next_counter}/{doc_date.strftime('%d-%m-%Y')}"

        # Create registry entry
        registry = Registry(
            CounterPerDocType=next_counter,
            DocName=doc_name,
            DocDate=doc_date,
            RegistryTypeId=registry_type_id,
            EmployeerId=employeer_id,
            IussedBy=username,
            IsDeleted=False,
        )
        db.session.add(registry)
        db.session.flush()  # Get the RegistroId

        return next_counter, doc_name, registry.RegistroId

    @staticmethod
    def create_hiring(data: dict) -> dict:
        """Create complete hiring record in a single transaction.

        data keys:
            # Personal
            cnp, name, surname, middle_name, birth_date, birth_town_id, sex,
            # Document
            doc_type_id, doc_serie, doc_number, doc_issued_by, doc_issue_date, doc_expire_date,
            # Address official
            addr_town_id, addr_street, addr_street2, addr_numero, addr_bloc, addr_scala, addr_piano, addr_apartment,
            # Address real (optional)
            addr2_town_id, addr2_street, addr2_street2, addr2_numero, addr2_bloc, addr2_scala, addr2_piano, addr2_apartment,
            # Contact
            phone, phone2, email, work_email,
            # Children: list of dicts
            children: [{name, birth_date, cnp, relative_type_id}],
            # Contract
            employeer_id, contract_type_id, hire_date, start_work_date, end_work_date_contract,
            hours_per_day, salary, test_period, core_code,
            # Assignment
            sub_cdc_id, function_id,
            # Registry
            registry_type_id, contract_number (optional override),
            # User info
            created_by_username
        """
        result = {'success': False, 'errors': []}

        try:
            # 1. Validate CNP
            cnp_result = validate_cnp(data['cnp'])
            if not cnp_result['valid']:
                result['errors'].append(f"CNP: {cnp_result['error']}")
                return result

            # 2. Check start_work_date > hire_date
            hire_date = data['hire_date']
            start_work = data['start_work_date']
            if start_work <= hire_date:
                result['errors'].append("La data di inizio lavoro deve essere successiva alla data di stipula del contratto.")
                return result

            # 3. Create or retrieve Employee
            employee = db.session.query(Employee).filter_by(EmployeeNID=data['cnp']).first()
            if employee:
                # Update existing employee data
                employee.EmployeeName = data['name']
                employee.EmployeeSurname = data['surname']
                if data.get('middle_name'):
                    pass  # No middle name field in Employee model currently
            else:
                employee = Employee(
                    EmployeeNID=data['cnp'],
                    EmployeeName=data['name'],
                    EmployeeSurname=data['surname'],
                    EmployeeBirthDate=cnp_result['birth_date'],
                    BirthCityId=data.get('birth_town_id'),
                    EmployeeSex=cnp_result['sex'] or data.get('sex', 'M'),
                )
                db.session.add(employee)
                db.session.flush()

            # 4. Generate contract number
            counter, doc_name, registry_id = HiringService.generate_contract_number(
                data['employeer_id'],
                data['registry_type_id'],
                hire_date,
                data.get('created_by_username', 'system')
            )

            # 5. Create EmployeeHireHistory
            hire_history = EmployeeHireHistory(
                EmployeeId=employee.EmployeeId,
                EmployeerId=data['employeer_id'],
                ContractTypeId=data['contract_type_id'],
                HireDate=hire_date,
                StartWorkDate=start_work,
                EndWorkDateContract=data.get('end_work_date_contract'),
                HourPerDay=data.get('hours_per_day', 8),
                HiringSalary=data.get('salary'),
                NoWorkContract=doc_name,
                TestPeriod=data.get('test_period', 90),
                CoreHiringCode=data.get('core_code'),
                IdRegistroCm=registry_id,
                SedeLavoroId=data['employeer_id'],
            )
            db.session.add(hire_history)
            db.session.flush()

            # 6. Create EmployeeCdcStory
            cdc_story = EmployeeCdcStory(
                EmployeeHireHistoryId=hire_history.EmployeeHireHistoryId,
                SubCdcId=data['sub_cdc_id'],
                FunctionId=data['function_id'],
            )
            db.session.add(cdc_story)

            # 7. Create official address
            address = EmployeeAddress(
                EmployeeId=employee.EmployeeId,
                TownAddressId=data.get('addr_town_id'),
                Street=data.get('addr_street'),
                Street2=data.get('addr_street2'),
                NumeroCivico=data.get('addr_numero'),
                Bloc=data.get('addr_bloc'),
                Scala=data.get('addr_scala'),
                Piano=data.get('addr_piano'),
                Apartment=data.get('addr_apartment'),
                TelephoneNo1=data.get('phone'),
                TelephoneNo2=data.get('phone2'),
                Email=data.get('email'),
                WorkEmail=data.get('work_email'),
            )
            db.session.add(address)

            # 8. Create identity document
            if data.get('doc_type_id'):
                doc = EmployeeDocument(
                    DocID=1,
                    EmployeeId=employee.EmployeeId,
                    EmployeeHireHistoryId=hire_history.EmployeeHireHistoryId,
                    FileName=f"ID_{employee.EmployeeNID}",
                    DocTypeId=data['doc_type_id'],
                    DocSerie=data.get('doc_serie'),
                    FileType='ref',
                    DocNumber=data.get('doc_number'),
                    IussedDateDoc=data.get('doc_issue_date'),
                    DocIsussedBy=data.get('doc_issued_by'),
                    ExpirationDateDoc=data.get('doc_expire_date'),
                )
                db.session.add(doc)

            # 9. Create children/dependents
            for child_data in data.get('children', []):
                if child_data.get('name'):
                    child = EmployeeChild(
                        EmployeeId=employee.EmployeeId,
                        ChildName=child_data['name'],
                        ChildBirthDate=child_data.get('birth_date', date.today()),
                        CNPChild=child_data.get('cnp', ''),
                        FamilyRelativeId=child_data.get('relative_type_id'),
                    )
                    db.session.add(child)

            db.session.commit()

            result['success'] = True
            result['employee_id'] = employee.EmployeeId
            result['hire_history_id'] = hire_history.EmployeeHireHistoryId
            result['contract_number'] = doc_name
            result['registry_id'] = registry_id

        except Exception as e:
            db.session.rollback()
            result['errors'].append(str(e))

        return result

    @staticmethod
    def generate_userid(name: str, surname: str) -> str:
        """Generate username: first letter of name + full surname (lowercase).
        If surname has two words, use only the first.
        """
        first_letter = name.strip()[0].lower() if name else 'x'
        surname_parts = surname.strip().split()
        main_surname = surname_parts[0].lower() if surname_parts else 'user'
        # Remove diacritics
        import unicodedata
        main_surname = ''.join(
            c for c in unicodedata.normalize('NFD', main_surname)
            if unicodedata.category(c) != 'Mn'
        )
        userid = f"{first_letter}.{main_surname}"

        # Ensure unique
        existing = db.session.query(User).filter_by(Username=userid).first()
        if existing:
            counter = 1
            while db.session.query(User).filter_by(Username=f"{userid}{counter}").first():
                counter += 1
            userid = f"{userid}{counter}"

        return userid

    @staticmethod
    def generate_random_password(length: int = 8) -> str:
        """Generate random alphanumeric password."""
        chars = string.ascii_letters + string.digits
        # Ensure at least 1 uppercase, 1 lowercase, 1 digit
        while True:
            pwd = ''.join(secrets.choice(chars) for _ in range(length))
            if (any(c.isupper() for c in pwd)
                    and any(c.islower() for c in pwd)
                    and any(c.isdigit() for c in pwd)):
                return pwd

    @staticmethod
    def create_user_account(employee: Employee, personal_email: str) -> tuple:
        """Create user account for the new employee.
        Returns (user, password).
        """
        username = HiringService.generate_userid(employee.EmployeeName, employee.EmployeeSurname)
        password = HiringService.generate_random_password()

        # Get email domain from settings
        domain = AppSetting.get_value('EMAIL_SERVICE_DOMAIN', 'company.com')
        work_email = f"{username}@{domain}"

        user = User(
            Username=username,
            Email=personal_email or work_email,
            EmployeeId=employee.EmployeeId,
            IsActive=True,
            MustChangePassword=True,
        )
        user.set_password(password)

        # Assign default role (employee)
        employee_role = db.session.query(Role).filter_by(RoleName='employee').first()
        if employee_role:
            user.roles.append(employee_role)

        db.session.add(user)
        db.session.commit()

        return user, password
