"""Exceptions used by Nest."""


class NestException(Exception):
    """Base class for all exceptions raised by Nest."""

    pass


class NestServiceException(Exception):
    """Raised when service is not available."""

    pass


class BadCredentialsException(Exception):
    """Raised when credentials are incorrect."""

    pass


class NotAuthenticatedException(Exception):
    """Raised when session is invalid."""

    pass


class GatewayTimeoutException(NestServiceException):
    """Raised when server times out."""

    pass


class BadGatewayException(NestServiceException):
    """Raised when server returns Bad Gateway."""

    pass


class InternalServerException(Exception):
    """Raised when session is invalid."""

    pass
