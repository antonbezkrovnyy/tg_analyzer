"""Custom exceptions for tg_analyzer."""


class AnalyzerError(Exception):
    """Base exception for all analyzer errors."""

    pass


class ConfigurationError(AnalyzerError):
    """Raised when configuration is invalid or missing."""

    pass


class DataNotFoundError(AnalyzerError):
    """Raised when requested data file is not found."""

    def __init__(self, chat: str, date: str, path: str) -> None:
        """Initialize DataNotFoundError.

        Args:
            chat: Chat name
            date: Date in YYYY-MM-DD format
            path: Full path to missing file
        """
        self.chat = chat
        self.date = date
        self.path = path
        super().__init__(
            f"Data file not found for chat '{chat}' on date '{date}': {path}"
        )


class DataValidationError(AnalyzerError):
    """Raised when data validation fails."""

    pass


class GigaChatAPIError(AnalyzerError):
    """Base exception for GigaChat API errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialize GigaChatAPIError.

        Args:
            message: Error message
            status_code: HTTP status code
        """
        self.status_code = status_code
        super().__init__(f"GigaChat API error: {message}")


class GigaChatAuthError(GigaChatAPIError):
    """Raised when GigaChat authentication fails."""

    def __init__(self, message: str = "Authentication failed") -> None:
        """Initialize GigaChatAuthError.

        Args:
            message: Error message
        """
        super().__init__(message, status_code=401)


class GigaChatRateLimitError(GigaChatAPIError):
    """Raised when GigaChat rate limit is exceeded."""

    def __init__(
        self, message: str = "Rate limit exceeded", retry_after: int | None = None
    ) -> None:
        """Initialize GigaChatRateLimitError.

        Args:
            message: Error message
            retry_after: Seconds to wait before retry
        """
        self.retry_after = retry_after
        super().__init__(message, status_code=429)


class GigaChatTimeoutError(GigaChatAPIError):
    """Raised when GigaChat API request times out."""

    def __init__(self, message: str = "Request timeout") -> None:
        """Initialize GigaChatTimeoutError.

        Args:
            message: Error message
        """
        super().__init__(message, status_code=None)


class AnalysisError(AnalyzerError):
    """Raised when analysis fails."""

    pass


class PromptBuildError(AnalyzerError):
    """Raised when prompt building fails."""

    pass
