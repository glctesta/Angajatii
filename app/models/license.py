"""
License management model.
Schema: app
"""
from typing import Optional
from datetime import datetime, date, timezone
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class License(Base):
    """Application license with tier validation."""
    __tablename__ = 'Licenses'
    __table_args__ = {'schema': 'app'}

    LicenseId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    LicenseKey: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    LicenseLevel: Mapped[str] = mapped_column(String(20), nullable=False)  # basic/professional/enterprise
    CompanyName: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    EmployeerId: Mapped[Optional[int]] = mapped_column(
        ForeignKey('dbo.Employeers.EmployeerId'), nullable=True
    )
    MaxUsers: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    ExpiresAt: Mapped[date] = mapped_column(Date, nullable=False)
    IsActive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    CreatedAt: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def is_valid(self) -> bool:
        return self.IsActive and not self.is_expired()

    def is_expired(self) -> bool:
        return date.today() > self.ExpiresAt

    def allows_level(self, level: str) -> bool:
        hierarchy = {'basic': 1, 'professional': 2, 'enterprise': 3}
        current_level = hierarchy.get(self.LicenseLevel.lower(), 0)
        required_level = hierarchy.get(level.lower(), 0)
        return current_level >= required_level

    def __repr__(self) -> str:
        return f"<License {self.LicenseKey} [{self.LicenseLevel}]>"
