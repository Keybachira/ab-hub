"""Custom exceptions for AB-hub."""


class ABHubError(Exception):
    """Base exception for all AB-hub errors."""


class AuthenticationError(ABHubError):
    """Raised when authentication fails or token is missing/invalid."""


class ConfigurationError(ABHubError):
    """Raised when configuration is invalid or missing."""


class GitHubAPIError(ABHubError):
    """Raised on GitHub API communication problems."""

    def __init__(self, message: str, status_code: int | None = None, response: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class RateLimitError(GitHubAPIError):
    """Raised when GitHub rate limit is exceeded."""

    def __init__(self, message: str, reset_at: int | None = None):
        super().__init__(message, status_code=403)
        self.reset_at = reset_at


class RepositoryNotFoundError(ABHubError):
    """Raised when a requested repository cannot be found locally or remotely."""


class DatabaseError(ABHubError):
    """Raised on database related failures."""


class ScanError(ABHubError):
    """Raised when a scan operation fails."""
