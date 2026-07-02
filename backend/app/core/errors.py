class PrescriptaError(Exception):
    """Base error for expected application failures."""


class NotFoundError(PrescriptaError):
    """Raised when a requested resource does not exist."""
