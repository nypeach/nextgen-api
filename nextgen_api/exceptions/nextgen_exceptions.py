"""
Custom exceptions for the NextGen API library.
"""


class NextGenAPIError(Exception):
    """Base exception class for NextGen API errors."""
    
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}
        super().__init__(self.message)
    
    def __str__(self):
        if self.status_code:
            return f"NextGen API Error {self.status_code}: {self.message}"
        return f"NextGen API Error: {self.message}"


class AuthenticationError(NextGenAPIError):
    """Raised when authentication fails."""
    pass


class TokenExpiredError(AuthenticationError):
    """Raised when the access token has expired."""
    pass


class ConfigurationError(NextGenAPIError):
    """Raised when there's a configuration issue."""
    pass


class ValidationError(NextGenAPIError):
    """Raised when request validation fails."""
    pass


class RateLimitError(NextGenAPIError):
    """Raised when rate limit is exceeded."""
    pass


class ServerError(NextGenAPIError):
    """Raised when the server returns a 5xx error."""
    pass


class ClientError(NextGenAPIError):
    """Raised when the client makes a bad request (4xx errors)."""
    pass


class NetworkError(NextGenAPIError):
    """Raised when there's a network connectivity issue."""
    pass