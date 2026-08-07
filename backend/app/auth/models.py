from enum import Enum

from pydantic import BaseModel


class Role(str, Enum):
    VIEWER = "viewer"
    ANALYST = "analyst"
    ADMINISTRATOR = "administrator"


class User(BaseModel):
    username: str
    role: Role
