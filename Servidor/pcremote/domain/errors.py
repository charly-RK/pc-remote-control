"""Domain errors. Each carries a stable code that is sent over the wire."""

from __future__ import annotations


class DomainError(Exception):
    """Base class for errors that can be reported to a client."""

    code = "EXECUTION_FAILED"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotAuthenticatedError(DomainError):
    code = "NOT_AUTHENTICATED"

    def __init__(self, message: str = "Not authenticated") -> None:
        super().__init__(message)


class InvalidPinError(DomainError):
    code = "INVALID_PIN"

    def __init__(self, message: str = "Invalid PIN") -> None:
        super().__init__(message)


class RateLimitedError(DomainError):
    code = "RATE_LIMITED"

    def __init__(self, message: str = "Too many attempts") -> None:
        super().__init__(message)


class InvalidPayloadError(DomainError):
    code = "INVALID_PAYLOAD"


class UnknownCommandError(DomainError):
    code = "UNKNOWN_COMMAND"


class UnsupportedActionError(DomainError):
    code = "UNSUPPORTED"


class ExecutionError(DomainError):
    code = "EXECUTION_FAILED"


class InvalidTokenError(DomainError):
    code = "INVALID_TOKEN"

    def __init__(self, message: str = "Invalid token") -> None:
        super().__init__(message)
