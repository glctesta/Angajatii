"""
Internationalization models — DB-backed translations.
Schema: app
"""
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Language(Base):
    """Supported UI language."""
    __tablename__ = 'Languages'
    __table_args__ = {'schema': 'app'}

    LanguageId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    LanguageCode: Mapped[str] = mapped_column(String(5), unique=True, nullable=False)
    LanguageName: Mapped[str] = mapped_column(String(50), nullable=False)
    IsActive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Language {self.LanguageCode} ({self.LanguageName})>"


class Translation(Base):
    """UI string translation stored in database."""
    __tablename__ = 'Translations'
    __table_args__ = (
        UniqueConstraint('TranslationKey', 'LanguageCode', name='uq_translation_key_lang'),
        {'schema': 'app'}
    )

    TranslationId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    TranslationKey: Mapped[str] = mapped_column(String(200), nullable=False)
    LanguageCode: Mapped[str] = mapped_column(
        String(5), ForeignKey('app.Languages.LanguageCode'), nullable=False
    )
    TranslationValue: Mapped[str] = mapped_column(Text, nullable=False)
    Module: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    UpdatedAt: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<Translation {self.TranslationKey} [{self.LanguageCode}]>"
