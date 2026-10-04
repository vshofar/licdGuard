class MapperException(Exception):
    """Base exception for mapper errors."""
    pass


class RequiredValueNotFoundException(MapperException):
    """Exception raised when a required field is missing or invalid in the payload."""
    pass


class NoContentException(MapperException):
    """Exception raised when the received payload is empty or null."""
    pass
