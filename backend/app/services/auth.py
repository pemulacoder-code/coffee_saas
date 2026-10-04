from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, verify_password
from app.models.user import User


async def get_user_by_email(
    session: AsyncSession,
    email: str,
) -> User | None:
    """Return a user by email, or None if the user does not exist."""

    result = await session.execute(
        select(User).where(User.email == email)
    )

    return result.scalar_one_or_none()


async def authenticate_user(
    session: AsyncSession,
    email: str,
    password: str,
) -> User | None:
    """
    Authenticate a user using email and password.

    Returns the User when authentication succeeds.
    Returns None when the credentials are invalid.
    """

    user = await get_user_by_email(
        session=session,
        email=email,
    )

    if user is None:
        return None

    if not user.is_active:
        return None

    if not verify_password(
        password,
        user.password_hash,
    ):
        return None

    return user


def create_user_access_token(user: User) -> str:
    """Create an access token for an authenticated user."""

    return create_access_token(
        subject=str(user.id),
    )
