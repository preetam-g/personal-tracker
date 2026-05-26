

class ForexError(Exception):
    """
    Base exception for all forex-related errors.
    """
    pass


class ExchangeRateAPIError(ForexError):
    """
    Raised when communication with the
    ExchangeRate API fails.
    """
    pass


class ExchangeRateAPIResponseError(ExchangeRateAPIError):
    """
    Raised when ExchangeRate API returns
    an application-level error response.
    """
    def __init__(self, message: str, error_type: str | None = None):
        self.error_type = error_type
        super().__init__(message)


class ExchangeRateUnavailable(ForexError):
    """
    Raised when an exchange rate
    cannot be retrieved or does not exist.
    """
    pass