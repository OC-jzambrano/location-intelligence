"""User service for user management operations."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import hash_password, verify_password
from src.models.user import User
from src.schemas.user import UserCreate, UserUpdate


class UserService:
    """
    Service class for user-related operations.

    Handles all database operations for users including CRUD
    and authentication helpers.
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize with database session.

        Args:
            db: Async database session.
        """
        self.db = db

    async def get_by_id(self, user_id: int) -> User | None:
        """
        Get a user by ID.

        Args:
            user_id: User's unique identifier.

        Returns:
            User if found, None otherwise.
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """
        Get a user by email address.

        Args:
            email: User's email address.

        Returns:
            User if found, None otherwise.
        """
        result = await self.db.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()

    async def create(self, user_data: UserCreate) -> User:
        """
        Create a new user.

        Args:
            user_data: User creation data.

        Returns:
            Created user instance.

        Raises:
            ValueError: If email is already registered.
        """
        # Check if email already exists
        existing = await self.get_by_email(user_data.email)
        if existing:
            raise ValueError("Email already registered")

        # Create user with hashed password
        user = User(
            email=user_data.email.lower(),
            hashed_password=hash_password(user_data.password),
            full_name=user_data.full_name,
        )

        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)

        return user

    async def update(self, user: User, user_data: UserUpdate) -> User:
        """
        Update a user's profile.

        Args:
            user: User to update.
            user_data: Update data.

        Returns:
            Updated user instance.
        """
        update_data = user_data.model_dump(exclude_unset=True)

        # Hash new password if provided
        if "password" in update_data and update_data["password"]:
            update_data["hashed_password"] = hash_password(update_data.pop("password"))
        elif "password" in update_data:
            del update_data["password"]

        # Apply updates
        for field, value in update_data.items():
            setattr(user, field, value)

        await self.db.flush()
        await self.db.refresh(user)

        return user

    async def delete(self, user: User) -> None:
        """
        Delete a user.

        Args:
            user: User to delete.
        """
        await self.db.delete(user)
        await self.db.flush()

    async def authenticate(self, email: str, password: str) -> User | None:
        """
        Authenticate a user by email and password.

        Args:
            email: User's email address.
            password: Plain text password.

        Returns:
            User if credentials are valid, None otherwise.
        """
        user = await self.get_by_email(email)

        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        if not user.is_active:
            return None

        return user

    async def set_active(self, user: User, is_active: bool) -> User:
        """
        Set user active status.

        Args:
            user: User to update.
            is_active: New active status.

        Returns:
            Updated user instance.
        """
        user.is_active = is_active
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def set_verified(self, user: User, is_verified: bool = True) -> User:
        """
        Set user email verification status.

        Args:
            user: User to update.
            is_verified: New verification status.

        Returns:
            Updated user instance.
        """
        user.is_verified = is_verified
        await self.db.flush()
        await self.db.refresh(user)
        return user
