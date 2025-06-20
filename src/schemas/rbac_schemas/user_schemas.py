from pydantic import EmailStr
from typing import Optional, List
from src.schemas.rbac_schemas.base_schema import SecureBaseSchema
from src.utils.rbac_utils.data_masking import mask_email

class UserBase(SecureBaseSchema):
    username: str

class UserPublic(UserBase):
    id: int

class UserPrivate(UserBase):
    id: int
    email: EmailStr

    # Apply column-level security and data masking policies
    SENSITIVE_FIELDS_PERMISSIONS = {
        "email": "user:read:email"  # Requires this permission to see the email
    }
    FIELD_MASKERS = {
        "email": mask_email # If permission is absent, mask the email
    }

class UserCreate(UserBase):
    email: EmailStr
    password: str

class UserListResponse(SecureBaseSchema):
    users: List[UserPublic]