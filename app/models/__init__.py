"""
Models package — imports all models to register them with SQLAlchemy.
"""
# Base
from .base import Base, TimestampMixin

# Geography (schema: Geo)
from .geography import Continent, Nation, County, Town

# Organization (schema: dbo)
from .organization import CostCenter, CdcSub, FunctionsStructure, Function, Employeer, ContractType, CodeCore

# Employee (schema: dbo)
from .employee import Employee, EmployeeHireHistory, EmployeeCdcStory

# Attendance (schema: dbo)
from .attendance import Shift, ShiftTimeTable, Badge, EmployeeBadgeHistory

# Address & Documents (schema: dbo)
from .address import EmployeeAddress, RelativeType, EmployeeChild, DocumentType, EmployeeDocument

# Authentication & Authorization (schema: app)
from .auth import User, Role, Permission, RolePermission, UserRole, UserCdcAccess, PasswordResetToken

# Licensing (schema: app)
from .license import License

# Audit (schema: app)
from .audit import AuditLog

# Resource Needs (schema: app)
from .needs import ResourceNeed, ResourceNeedSnapshot, ResourceRequest

# Internationalization (schema: app)
from .i18n import Language, Translation


__all__ = [
    # Base
    'Base', 'TimestampMixin',
    # Geography
    'Continent', 'Nation', 'County', 'Town',
    # Organization
    'CostCenter', 'CdcSub', 'FunctionsStructure', 'Function',
    'Employeer', 'ContractType', 'CodeCore',
    # Employee
    'Employee', 'EmployeeHireHistory', 'EmployeeCdcStory',
    # Attendance
    'Shift', 'ShiftTimeTable', 'Badge', 'EmployeeBadgeHistory',
    # Address
    'EmployeeAddress', 'RelativeType', 'EmployeeChild', 'DocumentType', 'EmployeeDocument',
    # Auth
    'User', 'Role', 'Permission', 'RolePermission', 'UserRole',
    'UserCdcAccess', 'PasswordResetToken',
    # License
    'License',
    # Audit
    'AuditLog',
    # Needs
    'ResourceNeed', 'ResourceNeedSnapshot', 'ResourceRequest',
    # i18n
    'Language', 'Translation',
]
