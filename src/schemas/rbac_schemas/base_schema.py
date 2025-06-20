from pydantic import BaseModel, ConfigDict
from typing import Set, Optional
from flask import g

from src.utils.rbac_utils.data_masking import mask_email

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class SecureBaseSchema(BaseSchema):
    """
    A base schema that implements Column-Level Security and Data Masking.
    It checks the user's permissions to determine which fields to include
    or mask in the final output.
    """
    
    # Define fields that are sensitive and require specific permissions to view unmasked.
    # Format: {"field_name": "permission:to:view:unmasked"}
    SENSITIVE_FIELDS_PERMISSIONS: dict = {}
    
    # Define masking functions for specific fields.
    # Format: {"field_name": masking_function}
    FIELD_MASKERS: dict = {}

    def model_dump(self, *args, **kwargs):
        """
        Overrides the default model_dump to apply security policies.
        """
        # Get the original data dictionary
        data = super().model_dump(*args, **kwargs)
        
        user_permissions: Set[str] = g.get('user_permissions_for_serialization', set())

        # Column-Level Security & Data Masking Logic
        for field, permission in self.SENSITIVE_FIELDS_PERMISSIONS.items():
            if field in data and permission not in user_permissions:
                # If user lacks permission, apply masking function if available, else remove field.
                if field in self.FIELD_MASKERS:
                    data[field] = self.FIELD_MASKERS[field](data[field])
                else:
                    # Fallback to removing the field if no masker is defined
                    del data[field]
        
        return data

# Helper function to be used in routes before serialization
def set_permissions_for_serialization():
    """Call this in a route to load user permissions into 'g' for the schema."""
    g.user_permissions_for_serialization = g.current_user.get_permissions() if g.get('current_user') else set()