class TempestException(Exception):
    """
    Base Tempest Exception

    To correctly use this class, inherit from it and define
    a 'message' property. That message will get printf'd
    with the keyword arguments provided to the constructor.
    """
    message = "An unknown exception occurred"

    def __init__(self, *args, **kwargs):
        try:
            self._error_string = self.message % kwargs
        except Exception:
            # at least get the core message out if something happened
            self._error_string = self.message
        if len(args) > 0:
            # If there is a non-kwarg parameter, assume it's the error
            # message or reason description and tack it on to the end
            # of the exception message
            # Convert all arguments into their string representations...
            args = ["%s" % arg for arg in args]
            self._error_string = (self._error_string +
                                  "\nDetails: %s" % '\n'.join(args))

    def __str__(self):
        return self._error_string


class InvalidConfiguration(TempestException):
    message = "Invalid Configuration"


class NotFound(TempestException):
    message = "Object not found"


class Unauthorized(TempestException):
    message = 'Unauthorized'


class TimeoutException(TempestException):
    message = "Request timed out"


class BuildErrorException(TempestException):
    message = "Server %(server_id)s failed to build and is in ERROR status"


class VolumeBuildErrorException(TempestException):
    message = "Volume %(volume_id)s failed to build and is in ERROR status"


class BadRequest(TempestException):
    message = "Bad request"


class AuthenticationFailure(TempestException):
    message = ("Authentication with user %(user)s and password "
               "%(password)s failed")


class EndpointNotFound(TempestException):
    message = "Endpoint not found"


class RateLimitExceeded(TempestException):
    message = ("Rate limit exceeded.\nMessage: %(message)s\n"
               "Details: %(details)s")


class OverLimit(TempestException):
    message = "Quota exceeded"


class ComputeFault(TempestException):
    message = "Got compute fault"


class Duplicate(TempestException):
    message = "An object with that identifier already exists"


class SSHTimeout(TempestException):
    message = ("Connection to the %(host)s via SSH timed out.\n"
                "User: %(user)s, Password: %(password)s")


class ServerUnreachable(TempestException):
    message = "The server is not reachable via the configured network"
