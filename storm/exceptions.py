class TimeoutException(Exception):
    """Exception on timeout"""
    def __repr__(self):
        return "Request timed out"


class BuildErrorException(Exception):
    """Exception on server build"""
    def __repr__(self):
        return "Server failed into error status"
