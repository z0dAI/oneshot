from enum import Enum

from pydantic import BaseModel


class Role(str, Enum):
    admin = "admin"
    recruiter = "recruiter"
    employee = "employee"


class Status(str, Enum):
    active = "active"
    pending = "pending"
    archived = "archived"


class ProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    avatar_url: str | None
    role: Role
    status: Status
    domain: str
    created_at: str
    updated_at: str


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    avatar_url: str | None = None


class UserUpdate(BaseModel):
    role: Role | None = None
    status: Status | None = None


class DomainCreate(BaseModel):
    domain: str
    activate_existing: bool = False


class DomainUpdate(BaseModel):
    is_active: bool


class DomainResponse(BaseModel):
    id: str
    domain: str
    added_by: str | None
    is_active: bool
    created_at: str


class PaginatedUsers(BaseModel):
    users: list[ProfileResponse]
    total: int
    page: int
    per_page: int
