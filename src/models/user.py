"""User model for authentication and user management."""

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class User(Base):
    """
    User model for authentication.

    Stores user credentials and profile information.
    Passwords are stored as bcrypt hashes.
    """

    # Override table name explicitly for clarity
    __tablename__ = "users"

    # Email is the primary identifier for login
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    # Hashed password (bcrypt)
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # User profile fields
    full_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Account status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Email verification status
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email!r})>"
