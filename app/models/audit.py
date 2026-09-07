"""
Audit logging model.
Schema: app
"""
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import String, Integer, BigInteger, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AuditLog(Base):
    """Tracks all significant actions in the application."""
    __tablename__ = 'AuditLog'
    __table_args__ = {'schema': 'app'}

    AuditId: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    UserId: Mapped[Optional[int]] = mapped_column(
        ForeignKey('app.Users.UserId'), nullable=True
    )
    Action: Mapped[str] = mapped_column(String(50), nullable=False)  # LOGIN/CREATE/UPDATE/DELETE/VIEW
    Module: Mapped[str] = mapped_column(String(50), nullable=False)
    EntityType: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    EntityId: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    OldValues: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    NewValues: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    IpAddress: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    UserAgent: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    CreatedAt: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.Action} {self.Module} by user {self.UserId}>"
