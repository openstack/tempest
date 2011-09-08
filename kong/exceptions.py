
class TimeoutException(Exception):
    """ Exception on timeout """
    def __repr__(self):
        return "Request Timed Out"


class ServerNotFound(KeyError):
    pass
