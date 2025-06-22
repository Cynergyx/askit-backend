import logging
from src.services.token_service import TokenService

# This is a mock email service. In production, you would replace this
# with a real email service like Flask-Mail, SendGrid, etc.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    def send_verification_email(user_email, user_id):
        salt = 'email-verification-salt'
        token = TokenService.generate_token(user_id, salt)
        verification_link = f"http://localhost:5000/api/auth/verify-email?token={token}" # Example link
        
        # In a real app, you would format this into an HTML email template.
        email_body = f"""
        Hello,

        Thank you for registering. Please verify your email by clicking the link below:
        {verification_link}

        This link will expire in 1 hour.

        If you did not register for this account, please ignore this email.
        """
        
        logger.info("---- MOCK EMAIL SENT ----")
        logger.info(f"To: {user_email}")
        logger.info(f"Subject: Verify Your Email Address")
        logger.info(f"Body: {email_body}")
        logger.info("-------------------------")