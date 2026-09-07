"""
Resource needs planning models.
Schema: app
"""
from typing import Optional
from datetime import datetime, date, timezone
from sqlalchemy import String, Integer, SmallInteger, BigInteger, DateTime, Date, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ResourceNeed(Base):
    """Headcount requirements per department/function/shift."""
    __tablename__ = 'ResourceNeeds'
    __table_args__ = {'schema': 'app'}

    NeedId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    SubCdcId: Mapped[int] = mapped_column(ForeignKey('dbo.CdcSub.SubCdcId'), nullable=False)
    FunctionId: Mapped[int] = mapped_column(ForeignKey('dbo.Functions.FunctionId'), nullable=False)
    ShiftId: Mapped[Optional[int]] = mapped_column(
        SmallInteger, ForeignKey('dbo.Shifts.ShiftId'), nullable=True
    )
    RequiredHeadcount: Mapped[int] = mapped_column(Integer, nullable=False)
    MinHeadcount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    EffectiveFrom: Mapped[date] = mapped_column(Date, nullable=False)
    EffectiveTo: Mapped[Optional[date]] = mapped_column(Date, nullable=True)  # NULL = current
    Notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    CreatedBy: Mapped[int] = mapped_column(ForeignKey('app.Users.UserId'), nullable=False)
    CreatedAt: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    UpdatedBy: Mapped[Optional[int]] = mapped_column(ForeignKey('app.Users.UserId'), nullable=True)
    UpdatedAt: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    sub_cdc = relationship("CdcSub", foreign_keys=[SubCdcId], lazy="select")
    function = relationship("Function", foreign_keys=[FunctionId], lazy="select")

    @property
    def is_current(self) -> bool:
        return self.EffectiveTo is None

    def __repr__(self) -> str:
        return f"<ResourceNeed cdc={self.SubCdcId} func={self.FunctionId} required={self.RequiredHeadcount}>"


class ResourceNeedSnapshot(Base):
    """Daily snapshot: needs vs actual headcount."""
    __tablename__ = 'ResourceNeedSnapshot'
    __table_args__ = (
        Index('ix_snapshot_date_cdc', 'SnapshotDate', 'SubCdcId'),
        {'schema': 'app'}
    )

    SnapshotId: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    SnapshotDate: Mapped[date] = mapped_column(Date, nullable=False)
    SubCdcId: Mapped[int] = mapped_column(ForeignKey('dbo.CdcSub.SubCdcId'), nullable=False)
    FunctionId: Mapped[int] = mapped_column(ForeignKey('dbo.Functions.FunctionId'), nullable=False)
    ShiftId: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    RequiredHeadcount: Mapped[int] = mapped_column(Integer, nullable=False)
    CurrentHeadcount: Mapped[int] = mapped_column(Integer, nullable=False)
    AbsentCount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    AvailableCount: Mapped[int] = mapped_column(Integer, nullable=False)
    CreatedAt: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    @property
    def gap_count(self) -> int:
        """Positive = understaffed, negative = overstaffed."""
        return self.RequiredHeadcount - self.AvailableCount

    def __repr__(self) -> str:
        return f"<Snapshot {self.SnapshotDate} cdc={self.SubCdcId} gap={self.gap_count}>"


class ResourceRequest(Base):
    """Personnel request when there's a staffing gap."""
    __tablename__ = 'ResourceRequests'
    __table_args__ = {'schema': 'app'}

    RequestId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    SubCdcId: Mapped[int] = mapped_column(ForeignKey('dbo.CdcSub.SubCdcId'), nullable=False)
    FunctionId: Mapped[int] = mapped_column(ForeignKey('dbo.Functions.FunctionId'), nullable=False)
    RequestedCount: Mapped[int] = mapped_column(Integer, nullable=False)
    Priority: Mapped[str] = mapped_column(
        String(10), default='normal', nullable=False
    )  # low/normal/high/critical
    Reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    Status: Mapped[str] = mapped_column(
        String(20), default='pending', nullable=False
    )  # pending/approved/rejected/fulfilled/cancelled
    RequestedBy: Mapped[int] = mapped_column(ForeignKey('app.Users.UserId'), nullable=False)
    RequestedAt: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    ApprovedBy: Mapped[Optional[int]] = mapped_column(ForeignKey('app.Users.UserId'), nullable=True)
    ApprovedAt: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    FulfilledAt: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    Notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    sub_cdc = relationship("CdcSub", foreign_keys=[SubCdcId], lazy="select")
    function = relationship("Function", foreign_keys=[FunctionId], lazy="select")

    def __repr__(self) -> str:
        return f"<ResourceRequest {self.RequestId} [{self.Status}] count={self.RequestedCount}>"
