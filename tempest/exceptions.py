class TimeoutException(Exception):
    """Exception on timeout"""
    def __repr__(self):
        return "Request timed out"


class BuildErrorException(Exception):
    """Exception on server build"""
    def __repr__(self):
        return "Server failed into error status"


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


class OverLimit(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)
