"""
Authentication, Authorization and Security models.
Schema: app
"""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, List

import bcrypt
from flask_login import UserMixin
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Table, Index, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


# --- Association Tables ---

class RolePermission(Base):
    """Many-to-many: Role ↔ Permission"""
    __tablename__ = 'RolePermissions'
    __table_args__ = {'schema': 'app'}

    RoleId: Mapped[int] = mapped_column(
        Integer, ForeignKey('app.Roles.RoleId'), primary_key=True
    )
    PermissionId: Mapped[int] = mapped_column(
        Integer, ForeignKey('app.Permissions.PermissionId'), primary_key=True
    )


class UserRole(Base):
    """Many-to-many: User ↔ Role"""
    __tablename__ = 'UserRoles'
    __table_args__ = {'schema': 'app'}

    UserId: Mapped[int] = mapped_column(
        Integer, ForeignKey('app.Users.UserId'), primary_key=True
    )
    RoleId: Mapped[int] = mapped_column(
        Integer, ForeignKey('app.Roles.RoleId'), primary_key=True
    )
    AssignedAt: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    AssignedBy: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('app.Users.UserId'), nullable=True
    )


class UserCdcAccess(Base):
    """Per-user CdC visibility restrictions."""
    __tablename__ = 'UserCdcAccess'
    __table_args__ = {'schema': 'app'}

    UserId: Mapped[int] = mapped_column(
        Integer, ForeignKey('app.Users.UserId'), primary_key=True
    )
    SubCdcId: Mapped[int] = mapped_column(
        Integer, ForeignKey('dbo.CdcSub.SubCdcId'), primary_key=True
    )


# --- Main Models ---

class User(Base, UserMixin):
    """Application user with secure authentication."""
    __tablename__ = 'Users'
    __table_args__ = (
        Index('ix_users_username', 'Username', unique=True),
        Index('ix_users_email', 'Email'),
        {'schema': 'app'}
    )

    UserId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    Username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    PasswordHash: Mapped[str] = mapped_column(String(255), nullable=False)
    EmployeeId: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('dbo.Employees.EmployeeId'), nullable=True
    )
    Email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    IsActive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    MustChangePassword: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    FailedAttempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    LockoutUntil: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    LastLoginAt: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    PreferredLanguage: Mapped[Optional[str]] = mapped_column(String(5), default='it', nullable=True)
    CreatedAt: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    UpdatedAt: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    IsSuperAdmin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary="app.UserRoles",
        primaryjoin="User.UserId == UserRole.UserId",
        secondaryjoin="Role.RoleId == UserRole.RoleId",
        back_populates="users",
        lazy="select"
    )
    employee: Mapped[Optional["Employee"]] = relationship(
        "Employee", foreign_keys=[EmployeeId], lazy="select"
    )
    cdc_access: Mapped[List["UserCdcAccess"]] = relationship(
        "UserCdcAccess", foreign_keys=[UserCdcAccess.UserId], lazy="select"
    )
    password_reset_tokens: Mapped[List["PasswordResetToken"]] = relationship(
        "PasswordResetToken", back_populates="user", lazy="dynamic"
    )

    # --- Flask-Login interface ---
    def get_id(self) -> str:
        return str(self.UserId)

    @property
    def is_active(self) -> bool:
        return self.IsActive

    # --- Password management ---
    def set_password(self, password: str) -> None:
        """Hash password with bcrypt."""
        self.PasswordHash = bcrypt.hashpw(
            password.encode('utf-8'), bcrypt.gensalt()
        ).decode('utf-8')

    def check_password(self, password: str) -> bool:
        """Verify password against bcrypt hash."""
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                self.PasswordHash.encode('utf-8')
            )
        except (ValueError, AttributeError):
            return False

    # --- Lockout management ---
    @property
    def is_locked_out(self) -> bool:
        if self.LockoutUntil is None:
            return False
        return datetime.now(timezone.utc) < self.LockoutUntil.replace(tzinfo=timezone.utc)

    def record_failed_login(self) -> None:
        """Increment failed attempts, lock after 5 failures."""
        self.FailedAttempts = (self.FailedAttempts or 0) + 1
        if self.FailedAttempts >= 5:
            self.LockoutUntil = datetime.now(timezone.utc) + timedelta(minutes=15)

    def record_successful_login(self) -> None:
        """Reset counters on successful login."""
        self.FailedAttempts = 0
        self.LockoutUntil = None
        self.LastLoginAt = datetime.now(timezone.utc)

    # --- Authorization ---
    def has_role(self, role_name: str) -> bool:
        return any(r.RoleName == role_name for r in self.roles)

    def has_any_role(self, *role_names: str) -> bool:
        return any(r.RoleName in role_names for r in self.roles)

    @property
    def is_super_admin(self) -> bool:
        return self.IsSuperAdmin

    def has_permission(self, permission_code: str) -> bool:
        if self.IsSuperAdmin:
            return True
        for role in self.roles:
            for perm in role.permissions:
                if perm.PermissionCode == permission_code:
                    return True
        return False

    def get_accessible_cdc_ids(self) -> List[int]:
        """Return list of SubCdcIds this user can access. Empty = all."""
        return [acc.SubCdcId for acc in self.cdc_access]

    def has_license_level(self, level: str) -> bool:
        """Check if any active license supports the given level."""
        from app.models.license import License
        from app.extensions import db
        hierarchy = {'basic': 1, 'professional': 2, 'enterprise': 3}
        required = hierarchy.get(level, 0)
        active = db.session.query(License).filter(
            License.IsActive == True,
            License.ExpiresAt >= datetime.now(timezone.utc).date()
        ).first()
        if active:
            return hierarchy.get(active.LicenseLevel, 0) >= required
        return False

    def __repr__(self) -> str:
        return f"<User {self.Username}>"


class Role(Base):
    """Authorization role."""
    __tablename__ = 'Roles'
    __table_args__ = {'schema': 'app'}

    RoleId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    RoleName: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    RoleDescription: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    IsSystemRole: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    CreatedAt: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary="app.UserRoles",
        primaryjoin="Role.RoleId == UserRole.RoleId",
        secondaryjoin="User.UserId == UserRole.UserId",
        back_populates="roles",
        lazy="select"
    )
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission", secondary="app.RolePermissions", back_populates="roles", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Role {self.RoleName}>"


class Permission(Base):
    """Granular permission."""
    __tablename__ = 'Permissions'
    __table_args__ = {'schema': 'app'}

    PermissionId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    PermissionCode: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    PermissionName: Mapped[str] = mapped_column(String(100), nullable=False)
    ModuleName: Mapped[str] = mapped_column(String(50), nullable=False)
    LicenseLevel: Mapped[str] = mapped_column(String(20), default='basic', nullable=False)
    CreatedAt: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        "Role", secondary="app.RolePermissions", back_populates="permissions", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Permission {self.PermissionCode}>"


class PasswordResetToken(Base):
    """Secure token for password reset flow."""
    __tablename__ = 'PasswordResetTokens'
    __table_args__ = {'schema': 'app'}

    TokenId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    UserId: Mapped[int] = mapped_column(
        Integer, ForeignKey('app.Users.UserId'), nullable=False
    )
    Token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    ExpiresAt: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    UsedAt: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    CreatedAt: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="password_reset_tokens")

    @property
    def is_valid(self) -> bool:
        """Token is valid if not used and not expired."""
        if self.UsedAt is not None:
            return False
        now = datetime.now(timezone.utc)
        expires = self.ExpiresAt.replace(tzinfo=timezone.utc) if self.ExpiresAt.tzinfo is None else self.ExpiresAt
        return now < expires

    def mark_used(self) -> None:
        self.UsedAt = datetime.now(timezone.utc)

    @staticmethod
    def generate_token(user_id: int, db_session, expiry_hours: int = 1) -> str:
        """Create a new password reset token for the given user."""
        token_str = secrets.token_urlsafe(32)
        token = PasswordResetToken(
            UserId=user_id,
            Token=token_str,
            ExpiresAt=datetime.now(timezone.utc) + timedelta(hours=expiry_hours)
        )
        db_session.add(token)
        db_session.commit()
        return token_str

    def __repr__(self) -> str:
        return f"<PasswordResetToken user={self.UserId} valid={self.is_valid}>"
