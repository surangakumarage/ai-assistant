from dataclasses import dataclass

from passlib.context import CryptContext

from app.auth.models import Role

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@dataclass
class HardcodedUser:
    username: str
    password_hash: str
    role: Role


# Hardcoded demo users (assignment Option A). Local/demo credentials only -
# never reuse this pattern for real user data.
_DEMO_CREDENTIALS: dict[str, tuple[str, Role]] = {
    "viewer": ("viewer123", Role.VIEWER),
    "analyst": ("analyst123", Role.ANALYST),
    "admin": ("admin123", Role.ADMINISTRATOR),
}

USERS: dict[str, HardcodedUser] = {
    username: HardcodedUser(username=username, password_hash=pwd_context.hash(password), role=role)
    for username, (password, role) in _DEMO_CREDENTIALS.items()
}


def get_user(username: str) -> HardcodedUser | None:
    return USERS.get(username)
