import kong.config
import kong.nova


class Manager(object):
    """Top-level object to access OpenStack resources."""

    def __init__(self, nova):
        self.nova = kong.nova.API(nova['host'],
                                  nova['port'],
                                  nova['ver'],
                                  nova['user'],
                                  nova['key'],
                                  nova['project'])
