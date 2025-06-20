import hashlib
import secrets
import string
import re
import bcrypt
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import jwt
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class PasswordSecurity:
    """Password security utilities"""
    
    # Password complexity requirements
    MIN_LENGTH = 8
    MAX_LENGTH = 128
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGITS = True
    REQUIRE_SPECIAL = True
    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    @staticmethod
    def generate_strong_password(length=12):
        """Generate a cryptographically strong password"""
        if length < PasswordSecurity.MIN_LENGTH:
            length = PasswordSecurity.MIN_LENGTH
        
        # Ensure at least one character from each required category
        password = []
        
        if PasswordSecurity.REQUIRE_UPPERCASE:
            password.append(secrets.choice(string.ascii_uppercase))
        if PasswordSecurity.REQUIRE_LOWERCASE:
            password.append(secrets.choice(string.ascii_lowercase))
        if PasswordSecurity.REQUIRE_DIGITS:
            password.append(secrets.choice(string.digits))
        if PasswordSecurity.REQUIRE_SPECIAL:
            password.append(secrets.choice(PasswordSecurity.SPECIAL_CHARS))
        
        # Fill the rest with random characters
        all_chars = string.ascii_letters + string.digits + PasswordSecurity.SPECIAL_CHARS
        for _ in range(length - len(password)):
            password.append(secrets.choice(all_chars))
        
        # Shuffle the password
        secrets.SystemRandom().shuffle(password)
        return ''.join(password)
    
    @staticmethod
    def validate_password_strength(password):
        """Validate password against security requirements"""
        errors = []
        
        if len(password) < PasswordSecurity.MIN_LENGTH:
            errors.append(f"Password must be at least {PasswordSecurity.MIN_LENGTH} characters long")
        
        if len(password) > PasswordSecurity.MAX_LENGTH:
            errors.append(f"Password must be no more than {PasswordSecurity.MAX_LENGTH} characters long")
        
        if PasswordSecurity.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if PasswordSecurity.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if PasswordSecurity.REQUIRE_DIGITS and not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        if PasswordSecurity.REQUIRE_SPECIAL and not re.search(f'[{re.escape(PasswordSecurity.SPECIAL_CHARS)}]', password):
            errors.append("Password must contain at least one special character")
        
        # Check for common patterns
        if re.search(r'(.)\1{2,}', password):
            errors.append("Password cannot contain repeated characters")
        
        if re.search(r'(012|123|234|345|456|567|678|789|890|abc|bcd|cde|def)', password.lower()):
            errors.append("Password cannot contain sequential characters")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def hash_password(password):
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password, hashed_password):
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password verification failed: {str(e)}")
            return False
    
    @staticmethod
    def check_password_breach(password):
        """Check if password has been breached using SHA-1 prefix"""
        # This would integrate with HaveIBeenPwned API in production
        sha1_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
        prefix = sha1_hash[:5]
        suffix = sha1_hash[5:]
        
        # In production, make API call to https://api.pwnedpasswords.com/range/{prefix}
        # For now, return False (not breached)
        return False

class TokenSecurity:
    """Token generation and validation utilities"""
    
    @staticmethod
    def generate_secure_token(length=32):
        """Generate a cryptographically secure token"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_api_key(prefix="ak_"):
        """Generate API key with prefix"""
        token = TokenSecurity.generate_secure_token(40)
        return f"{prefix}{token}"
    
    @staticmethod
    def generate_reset_token():
        """Generate password reset token"""
        return TokenSecurity.generate_secure_token(48)
    
    @staticmethod
    def create_jwt_token(payload, secret_key, expiry_hours=24):
        """Create JWT token with expiration"""
        payload['exp'] = datetime.utcnow() + timedelta(hours=expiry_hours)
        payload['iat'] = datetime.utcnow()
        return jwt.encode(payload, secret_key, algorithm='HS256')
    
    @staticmethod
    def verify_jwt_token(token, secret_key):
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            return payload, None
        except jwt.ExpiredSignatureError:
            return None, "Token has expired"
        except jwt.InvalidTokenError:
            return None, "Invalid token"

class DataEncryption:
    """Data encryption utilities"""
    
    @staticmethod
    def generate_key():
        """Generate encryption key"""
        return Fernet.generate_key()
    
    @staticmethod
    def derive_key_from_password(password, salt=None):
        """Derive encryption key from password"""
        if salt is None:
            salt = secrets.token_bytes(32)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt
    
    @staticmethod
    def encrypt_data(data, key):
        """Encrypt data using Fernet symmetric encryption"""
        try:
            f = Fernet(key)
            if isinstance(data, str):
                data = data.encode('utf-8')
            encrypted_data = f.encrypt(data)
            return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise
    
    @staticmethod
    def decrypt_data(encrypted_data, key):
        """Decrypt data using Fernet symmetric encryption"""
        try:
            f = Fernet(key)
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = f.decrypt(encrypted_bytes)
            return decrypted_data.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise
    
    @staticmethod
    def hash_data(data, algorithm='sha256'):
        """Hash data using specified algorithm"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        if algorithm == 'sha256':
            return hashlib.sha256(data).hexdigest()
        elif algorithm == 'sha512':
            return hashlib.sha512(data).hexdigest()
        elif algorithm == 'md5':
            return hashlib.md5(data).hexdigest()
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")

class InputSanitization:
    """Input sanitization and validation utilities"""
    
    @staticmethod
    def sanitize_string(input_string, max_length=None, allow_html=False):
        """Sanitize string input"""
        if not isinstance(input_string, str):
            return ""
        
        # Remove null bytes
        sanitized = input_string.replace('\x00', '')
        
        # Strip whitespace
        sanitized = sanitized.strip()
        
        # Remove HTML tags if not allowed
        if not allow_html:
            sanitized = re.sub(r'<[^>]+>', '', sanitized)
        
        # Limit length
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_domain(domain):
        """Validate domain format"""
        pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
        return re.match(pattern, domain) is not None
    
    @staticmethod
    def sanitize_sql_input(input_string):
        """Basic SQL injection prevention"""
        if not isinstance(input_string, str):
            return ""
        
        # Remove common SQL injection patterns
        dangerous_patterns = [
            r"'.*'",
            r'".*"',
            r'--',
            r'/\*.*\*/',
            r'union\s+select',
            r'drop\s+table',
            r'delete\s+from',
            r'insert\s+into',
            r'update\s+set'
        ]
        
        sanitized = input_string
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    @staticmethod
    def validate_uuid(uuid_string):
        """Validate UUID format"""
        pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        return re.match(pattern, uuid_string, re.IGNORECASE) is not None

class SecurityHeaders:
    """Security header utilities"""
    
    @staticmethod
    def get_security_headers():
        """Get recommended security headers"""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'",
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
        }
    
    @staticmethod
    def apply_security_headers(response):
        """Apply security headers to Flask response"""
        headers = SecurityHeaders.get_security_headers()
        for header, value in headers.items():
            response.headers[header] = value
        return response

class RateLimiting:
    """Rate limiting utilities"""
    
    @staticmethod
    def create_rate_limit_key(user_id, endpoint, window='minute'):
        """Create rate limit key"""
        timestamp = datetime.utcnow()
        
        if window == 'minute':
            time_window = timestamp.strftime('%Y-%m-%d-%H-%M')
        elif window == 'hour':
            time_window = timestamp.strftime('%Y-%m-%d-%H')
        elif window == 'day':
            time_window = timestamp.strftime('%Y-%m-%d')
        else:
            time_window = timestamp.strftime('%Y-%m-%d-%H-%M')
        
        return f"rate_limit:{user_id}:{endpoint}:{time_window}"
    
    @staticmethod
    def check_rate_limit(redis_client, key, limit, window_seconds=60):
        """Check if rate limit is exceeded"""
        try:
            current_count = redis_client.get(key)
            if current_count is None:
                redis_client.setex(key, window_seconds, 1)
                return False, 1
            
            current_count = int(current_count)
            if current_count >= limit:
                return True, current_count
            
            redis_client.incr(key)
            return False, current_count + 1
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {str(e)}")
            return False, 0

def generate_csrf_token():
    """Generate CSRF token"""
    return TokenSecurity.generate_secure_token(32)

def validate_csrf_token(token, session_token):
    """Validate CSRF token"""
    return secrets.compare_digest(token, session_token)

def secure_compare(a, b):
    """Timing-safe string comparison"""
    return secrets.compare_digest(str(a), str(b))

def init_security_utils():
    """Initialize security utilities"""
    logger.info("Security utilities initialized")