"""
Application Settings model.
Stores configurable parameters managed by admin.
"""
from sqlalchemy import String, Integer, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from datetime import datetime
from .base import Base


class AppSetting(Base):
    __tablename__ = 'AppSettings'
    __table_args__ = {'schema': 'app'}

    SettingId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    SettingKey: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    SettingValue: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    SettingType: Mapped[str] = mapped_column(String(20), nullable=False, default='string')  # string, int, path, bool
    Category: Mapped[str] = mapped_column(String(50), nullable=False, default='general')  # general, email, documents, medical
    Description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    UpdatedBy: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    UpdatedAt: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    @staticmethod
    def get_value(key: str, default: str = None) -> str:
        """Get setting value by key. Must be called within app context."""
        from app.extensions import db
        setting = db.session.query(AppSetting).filter_by(SettingKey=key).first()
        if setting and setting.SettingValue is not None:
            return setting.SettingValue
        return default

    @staticmethod
    def set_value(key: str, value: str, user_id: int = None):
        """Set setting value by key."""
        from app.extensions import db
        setting = db.session.query(AppSetting).filter_by(SettingKey=key).first()
        if setting:
            setting.SettingValue = value
            setting.UpdatedBy = user_id
            setting.UpdatedAt = datetime.utcnow()
        else:
            setting = AppSetting(SettingKey=key, SettingValue=value, UpdatedBy=user_id)
            db.session.add(setting)
        db.session.commit()


# Default settings to seed
DEFAULT_SETTINGS = [
    {'SettingKey': 'DOCUMENT_TEMPLATE_PATH', 'SettingValue': r'L:\\', 'SettingType': 'path',
     'Category': 'documents', 'Description': 'Path ai template sorgente .docx'},
    {'SettingKey': 'DOCUMENT_OUTPUT_PATH', 'SettingValue': r'L:\\Employees\\Documenti\\', 'SettingType': 'path',
     'Category': 'documents', 'Description': 'Path output documenti generati ({anno}/{EmployeeId}/)'},
    {'SettingKey': 'EMAIL_SERVICE_DOMAIN', 'SettingValue': 'vandewiele.com', 'SettingType': 'string',
     'Category': 'email', 'Description': 'Dominio email di servizio (es. vandewiele.com)'},
    {'SettingKey': 'COMPANY_LOGO_PATH', 'SettingValue': '', 'SettingType': 'path',
     'Category': 'general', 'Description': 'Path logo aziendale per documenti'},
    {'SettingKey': 'CONTRACT_NUMBER_START', 'SettingValue': '1', 'SettingType': 'int',
     'Category': 'documents', 'Description': 'Numero iniziale contatore contratti'},
    {'SettingKey': 'COMPANY_NAME', 'SettingValue': 'Vandewiele Romania', 'SettingType': 'string',
     'Category': 'general', 'Description': 'Nome azienda principale'},
]
