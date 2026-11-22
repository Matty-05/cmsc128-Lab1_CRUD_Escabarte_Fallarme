import re

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,30}$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8


def validate_required(fields):
    """
    fields: dict of {field_name: value}, e.g. {"display_name": "Ralph"}
    Returns a dict of {field_name: message} for every blank value, so
    templates can show each message under the right input.
    """
    errors = {}
    for name, value in fields.items():
        if not value or not value.strip():
            label = name.replace("_", " ").capitalize()
            errors[name] = f"{label} is required."
    return errors


def is_valid_username(username):
    """3-30 chars, letters/numbers/underscores only."""
    return bool(USERNAME_PATTERN.match(username))


def is_valid_email(email):
    """Simple shape check, not full RFC validation."""
    return bool(EMAIL_PATTERN.match(email))


def password_error(password):
    """Returns an error message if the password is too short, otherwise None."""
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
    return None