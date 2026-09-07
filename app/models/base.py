"""
Base model classes and mixins.
Base is imported from extensions to avoid circular imports.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column

# Re-export Base from extensions (where it's defined to avoid circular imports)
from app.extensions import Base


class TimestampMixin:
    """Mixin for adding created_at and updated_at timestamps."""
    created_at: Mapped[Optional[datetime]] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )
