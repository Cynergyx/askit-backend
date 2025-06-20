def mask_email(email: str) -> str:
    """Masks an email address, e.g., u***r@e****e.com"""
    if not email or '@' not in email:
        return ""
    local, domain = email.split('@', 1)
    return f"{local[0]}***{local[-1]}@{domain[0]}***{domain.split('.')[-1]}"

def mask_string(s: str) -> str:
    """Masks a string, showing only first and last characters."""
    if len(s) < 4:
        return "****"
    return f"{s[0]}***{s[-1]}"