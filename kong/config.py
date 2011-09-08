import ConfigParser


class NovaConfig(object):
    """Provides configuration information for connecting to Nova."""

    def __init__(self, conf):
        """Initialize a Nova-specific configuration object."""
        self.conf = conf

    def get(self, item_name, default_value):
        try:
            return self.conf.get("nova", item_name)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            return default_value

    @property
    def host(self):
        """Host for the Nova HTTP API. Defaults to 127.0.0.1."""
        return self.get("host", "127.0.0.1")

    @property
    def port(self):
        """Port for the Nova HTTP API. Defaults to 8774."""
        return int(self.get("port", 8774))

    @property
    def username(self):
        """Username to use for Nova API requests. Defaults to 'admin'."""
        return self.get("user", "admin")

    @property
    def base_url(self):
        """Base of the HTTP API URL. Defaults to '/v1.1'."""
        return self.get("base_url", "/v1.1")

    @property
    def project_id(self):
        """Base of the HTTP API URL. Defaults to '/v1.1'."""
        return self.get("project_id", "admin")

    @property
    def api_key(self):
        """API key to use when authenticating. Defaults to 'admin_key'."""
        return self.get("api_key", "admin_key")

    @property
    def ssh_timeout(self):
        """Timeout in seconds to use when connecting via ssh."""
        return float(self.get("ssh_timeout", 300))

    @property
    def build_timeout(self):
        """Timeout in seconds to use when connecting via ssh."""
        return float(self.get("build_timeout", 300))



class EnvironmentConfig(object):
    def __init__(self, conf):
        """Initialize a Environment-specific configuration object."""
        self.conf = conf

    def get(self, item_name, default_value):
        try:
            return self.conf.get("environment", item_name)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            return default_value

    @property
    def image_ref(self):
        """Valid imageRef to use """
        return self.get("image_ref", 3);

    @property
    def image_ref_alt(self):
        """Valid imageRef to rebuild images with"""
        return self.get("image_ref_alt", 3);

    @property
    def flavor_ref(self):
        """Valid flavorRef to use"""
        return self.get("flavor_ref", 1);

    @property
    def flavor_ref_alt(self):
        """Valid flavorRef to resize images with"""
        return self.get("flavor_ref_alt", 2);

    @property
    def multi_node(self):
        """ Does the test environment have more than one compute node """
        return self.get("multi_node", 'false') != 'false'


class StackConfig(object):
    """Provides `kong` configuration information."""

    _path = None

    def __init__(self, path=None):
        """Initialize a configuration from a path."""
        self._path = path or self._path
        self._conf = self.load_config(self._path)
        self.nova = NovaConfig(self._conf)
        self.env = EnvironmentConfig(self._conf)

    def load_config(self, path=None):
        """Read configuration from given path and return a config object."""
        config = ConfigParser.SafeConfigParser()
        config.read(path)
        return config
