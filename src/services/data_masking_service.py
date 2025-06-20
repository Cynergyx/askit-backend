import re
import hashlib
from cryptography.fernet import Fernet
import base64

class DataMaskingService:
    @staticmethod
    def mask_data(data, masking_policies):
        """Apply data masking policies to data"""
        if not data or not masking_policies:
            return data
        
        # Handle different data types
        if isinstance(data, dict):
            return DataMaskingService._mask_dict(data, masking_policies)
        elif isinstance(data, list):
            return [DataMaskingService._mask_dict(item, masking_policies) for item in data]
        else:
            return data
    
    @staticmethod
    def _mask_dict(data_dict, masking_policies):
        """Mask fields in a dictionary based on policies"""
        masked_data = data_dict.copy()
        
        for policy in masking_policies:
            field_name = policy.column_name
            
            if field_name in masked_data:
                original_value = masked_data[field_name]
                
                if original_value is not None:
                    masked_value = DataMaskingService._apply_masking(
                        original_value,
                        policy.masking_type,
                        policy.masking_pattern
                    )
                    masked_data[field_name] = masked_value
        
        return masked_data
    
    @staticmethod
    def _apply_masking(value, masking_type, pattern=None):
        """Apply specific masking technique to a value"""
        if value is None:
            return None
        
        str_value = str(value)
        
        if masking_type == 'FULL':
            return '*' * len(str_value)
        
        elif masking_type == 'PARTIAL':
            if pattern:
                # Apply custom pattern (e.g., "XXX-XX-XXXX" for SSN)
                return DataMaskingService._apply_pattern_mask(str_value, pattern)
            else:
                # Default partial masking (show first and last 2 characters)
                if len(str_value) <= 4:
                    return '*' * len(str_value)
                else:
                    return str_value[:2] + '*' * (len(str_value) - 4) + str_value[-2:]
        
        elif masking_type == 'HASH':
            return hashlib.sha256(str_value.encode()).hexdigest()[:16]
        
        elif masking_type == 'ENCRYPT':
            # Simple encryption (in production, use proper key management)
            key = Fernet.generate_key()
            f = Fernet(key)
            encrypted = f.encrypt(str_value.encode())
            return base64.b64encode(encrypted).decode()
        
        else:
            return str_value
    
    @staticmethod
    def _apply_pattern_mask(value, pattern):
        """Apply pattern-based masking"""
        # Simple pattern application
        # X = mask character, others are literal
        result = ""
        value_idx = 0
        
        for char in pattern:
            if char == 'X':
                if value_idx < len(value):
                    result += 'X'
                    value_idx += 1
                else:
                    result += 'X'
            else:
                result += char
        
        return result