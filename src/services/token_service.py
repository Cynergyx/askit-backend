from itsdangerous import URLSafeTimedSerializer
from flask import current_app

class TokenService:
    @staticmethod
    def generate_token(data, salt):
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return serializer.dumps(data, salt=salt)

    @staticmethod
    def verify_token(token, salt, max_age_seconds=3600):
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            data = serializer.loads(
                token,
                salt=salt,
                max_age=max_age_seconds
            )
            return data
        except Exception:
            return None