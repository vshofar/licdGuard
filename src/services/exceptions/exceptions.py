class ComprasnetException(Exception):
    """Base exception for Comprasnet API errors."""
    pass


class BadRequest(ComprasnetException):
    """Exception raised for HTTP 400 Bad Request."""
    pass


class ResourceNotFound(ComprasnetException):
    """Exception raised for HTTP 404 Not Found."""
    pass


class InternalError(ComprasnetException):
    """Exception raised for HTTP 500 Internal Server Error."""
    pass


class UnknownRequestException(ComprasnetException):
    """Exception raised for unmapped HTTP status codes."""
    pass
