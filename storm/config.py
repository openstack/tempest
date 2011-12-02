import ConfigParser
import logging
import os

LOG = logging.getLogger(__name__)


class NovaConfig(object):
    """Provides configuration information for connecting to Nova."""

    def __init__(self, conf):
        """Initialize a Nova-specific configuration object"""
        self.conf = conf

    def get(self, item_name, default_value):
        try:
            return self.conf.get("nova", item_name)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            return default_value

    @property
    def host(self):
        """Host IP for making Nova API requests. Defaults to '127.0.0.1'."""
        return self.get("host", "127.0.1")

    @property
    def port(self):
        """Listen port of the Nova service."""
        return self.get("port", "8773")

    @property
    def apiVer(self):
        """Version of the API"""
        return self.get("apiVer", "v1.1")

    @property
    def path(self):
        """Path of API request"""
        return self.get("path", "/")

    def params(self):
        """Parameters to be passed with the API request"""
        return self.get("params", "")

    @property
    def username(self):
        """Username to use for Nova API requests. Defaults to 'admin'."""
        return self.get("user", "admin")

    @property
    def tenant_name(self):
        """Tenant name to use for Nova API requests. Defaults to 'admin'."""
        return self.get("tenant_name", "admin")

    @property
    def api_key(self):
        """API key to use when authenticating. Defaults to 'admin_key'."""
        return self.get("api_key", "admin_key")

    @property
    def build_interval(self):
        """Time in seconds between build status checks."""
        return float(self.get("build_interval", 10))

    @property
    def ssh_timeout(self):
        """Timeout in seconds to use when connecting via ssh."""
        return float(self.get("ssh_timeout", 300))

    @property
    def build_timeout(self):
        """Timeout in seconds to wait for an entity to build."""
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
        return self.get("image_ref", 3)

    @property
    def image_ref_alt(self):
        """Valid imageRef to rebuild images with"""
        return self.get("image_ref_alt", 3)

    @property
    def flavor_ref(self):
        """Valid flavorRef to use"""
        return self.get("flavor_ref", 1)

    @property
    def flavor_ref_alt(self):
        """Valid flavorRef to resize images with"""
        return self.get("flavor_ref_alt", 2)

    @property
    def resize_available(self):
        """ Does the test environment support resizing """
        return self.get("resize_available", 'false') != 'false'

    @property
    def create_image_enabled(self):
        """ Does the test environment support resizing """
        return self.get("create_image_enabled", 'false') != 'false'

    @property
    def authentication(self):
        """ What auth method does the environment use (basic|keystone) """
        return self.get("authentication", 'keystone')


class StormConfig(object):
    """Provides OpenStack configuration information."""

    def __init__(self, conf_dir, conf_file):
        """
        Initialize a configuration from a conf directory and conf file.

        :param conf_dir: Directory to look for config files
        :param conf_file: Name of config file to use
        """
        path = os.path.join(conf_dir, conf_file)

        if not os.path.exists(path):
            msg = "Config file %(path)s not found" % locals()
            raise RuntimeError(msg)

        self._conf = self.load_config(path)
        self.nova = NovaConfig(self._conf)
        self.env = EnvironmentConfig(self._conf)

    def load_config(self, path):
        """Read configuration from given path and return a config object."""
        config = ConfigParser.SafeConfigParser()
        config.read(path)
        return config
