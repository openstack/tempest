class TimeoutException(Exception):
    """Exception on timeout"""
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class BuildErrorException(Exception):
    """Server entered ERROR status unintentionally"""
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class BadRequest(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class AuthenticationFailure(Exception):
    msg = ("Authentication with user %(user)s and password "
           "%(password)s failed.")

    def __init__(self, **kwargs):
        self.message = self.msg % kwargs


class EndpointNotFound(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class OverLimit(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class ComputeFault(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)
