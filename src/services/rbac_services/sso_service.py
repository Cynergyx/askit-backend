from abc import ABC, abstractmethod

class SSOServiceStrategy(ABC):
    """Abstract base class for SSO strategies."""
    @abstractmethod
    def get_redirect_url(self):
        pass

    @abstractmethod
    def handle_callback(self, callback_data):
        pass

class OAuth2Strategy(SSOServiceStrategy):
    def __init__(self, provider_config):
        self.config = provider_config # e.g., client_id, client_secret, endpoints

    def get_redirect_url(self):
        # Logic to build the authorization URL for Google, Okta, etc.
        print(f"Redirecting to {self.config['name']} OAuth2 provider...")
        return "https://provider.com/oauth2/auth?..."

    def handle_callback(self, callback_data):
        # Logic to exchange the code for a token, get user info,
        # and then find or create a user in our system.
        print(f"Handling callback from {self.config['name']}...")
        user_info = {"email": "sso_user@example.com", "name": "SSO User"}
        # Find user by email, if not found, maybe provision one.
        # Then generate our own JWT for them.
        return "our_jwt_for_sso_user"

class SAMLStrategy(SSOServiceStrategy):
    def get_redirect_url(self):
        print("Initiating SAML SSO flow...")
        return "https://idp.com/saml/sso?..."

    def handle_callback(self, callback_data):
        # Logic to parse the SAML assertion, validate it,
        # extract user attributes, and provision/log in the user.
        print("Handling SAML assertion...")
        return "our_jwt_for_saml_user"

class SSOService:
    """Context that uses the SSO strategy."""
    def __init__(self, strategy: SSOServiceStrategy):
        self._strategy = strategy

    def login(self):
        return self._strategy.get_redirect_url()
    
    def callback(self, data):
        return self._strategy.handle_callback(data)

# Example usage (in a route):
# okta_config = {"name": "Okta", ...}
# sso_service = SSOService(OAuth2Strategy(okta_config))
# return redirect(sso_service.login())