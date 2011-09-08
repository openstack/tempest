import kong.config
import kong.nova


class Manager(object):
    """Top-level object to access OpenStack resources."""

    def __init__(self):
        self.config = kong.config.StackConfig()
        self.nova = kong.nova.API(self.config.nova.host,
                                    self.config.nova.port,
                                    self.config.nova.base_url,
                                    self.config.nova.username,
                                    self.config.nova.api_key,
                                    self.config.nova.project_id)
