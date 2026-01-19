"""
SQLAlchemy base model with common columns and utilities.

All models should inherit from Base to get automatic ID, timestamps,
and other common functionality.
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    
    Provides:
    - Automatic table naming from class name
    - Common ID column
    - Created/updated timestamps
    - Useful repr and dict conversion
    """
    
    # Generate __tablename__ automatically from class name
    @declared_attr.directive
    @classmethod
    def __tablename__(cls) -> str:
        """Generate table name from class name (snake_case)."""
        name = cls.__name__
        # Convert CamelCase to snake_case
        result = [name[0].lower()]
        for char in name[1:]:
            if char.isupper():
                result.append("_")
                result.append(char.lower())
            else:
                result.append(char)
        return "".join(result) + "s"  # Pluralize
    
    # Common columns
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    
    def __repr__(self) -> str:
        """Generate a useful repr string."""
        class_name = self.__class__.__name__
        attrs = []
        
        # Include id and a few key attributes
        if hasattr(self, "id"):
            attrs.append(f"id={self.id}")
        
        # Include email if present (common identifier)
        if hasattr(self, "email"):
            attrs.append(f"email={self.email!r}")
        
        # Include name if present
        if hasattr(self, "name"):
            attrs.append(f"name={self.name!r}")
        
        return f"<{class_name}({', '.join(attrs)})>"
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert model to dictionary.
        
        Excludes private attributes and SQLAlchemy internals.
        """
        result = {}
        
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            
            # Convert datetime to ISO format
            if isinstance(value, datetime):
                value = value.isoformat()
            
            result[column.name] = value
        
        return result


# Import all models here to ensure they're registered with Base
# This is used by Alembic for migrations
def import_models() -> None:
    """Import all models to register them with SQLAlchemy."""
    from src import models  # noqa: F401
