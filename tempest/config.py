import ConfigParser
import logging
import os
from tempest.common.utils import data_utils

LOG = logging.getLogger(__name__)


class IdentityConfig(object):
    """Provides configuration information for authenticating with Keystone."""

    def __init__(self, conf):
        """Initialize an Identity-specific configuration object"""
        self.conf = conf

    def get(self, item_name, default_value=None):
        try:
            return self.conf.get("identity", item_name)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            return default_value

    @property
    def host(self):
        """Host IP for making Identity API requests."""
        return self.get("host", "127.0.0.1")

    @property
    def port(self):
        """Port for the Identity service."""
        return self.get("port", "8773")

    @property
    def api_version(self):
        """Version of the Identity API"""
        return self.get("api_version", "v1.1")

    @property
    def path(self):
        """Path of API request"""
        return self.get("path", "/")

    @property
    def auth_url(self):
        """The Identity URL (derived)"""
        auth_url = data_utils.build_url(self.host,
                                        self.port,
                                        self.api_version,
                                        self.path,
                                        use_ssl=self.use_ssl)
        return auth_url

    @property
    def use_ssl(self):
        """Specifies if we are using https."""
        return self.get("use_ssl", 'false') != 'false'

    @property
    def username(self):
        """Username to use for Identity API requests."""
        return self.get("user", None)

    @property
    def tenant_name(self):
        """Tenant name to use for Identity API requests."""
        return self.get("tenant_name", None)

    @property
    def password(self):
        """Password to use when authenticating."""
        return self.get("password", None)

    @property
    def strategy(self):
        """Which auth method does the environment use? (basic|keystone)"""
        return self.get("strategy", 'keystone')


class ComputeConfig(object):
    def __init__(self, conf):
        """Initialize a Compute-specific configuration object."""
        self.conf = conf

    def get(self, item_name, default_value):
        try:
            return self.conf.get("compute", item_name)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            return default_value

    @property
    def image_ref(self):
        """Valid primary image to use in tests."""
        return self.get("image_ref", 'e7ddc02e-92fa-4f82-b36f-59b39bf66a67')

    @property
    def image_ref_alt(self):
        """Valid secondary image reference to be used in tests."""
        return self.get("image_ref_alt", '346f4039-a81e-44e0-9223-4a3d13c907')

    @property
    def flavor_ref(self):
        """Valid primary flavor to use in tests."""
        return self.get("flavor_ref", 1)

    @property
    def flavor_ref_alt(self):
        """Valid secondary flavor to be used in tests."""
        return self.get("flavor_ref_alt", 2)

    @property
    def resize_available(self):
        """Does the test environment support resizing?"""
        return self.get("resize_available", 'false') != 'false'

    @property
    def create_image_enabled(self):
        """Does the test environment support snapshots?"""
        return self.get("create_image_enabled", 'false') != 'false'

    @property
    def release_name(self):
        """Which release is this?"""
        return self.get("release_name", 'essex')

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

    @property
    def catalog_type(self):
        """Catalog type of the Compute service."""
        return self.get("catalog_type", 'compute')


class ImagesConfig(object):
    """
    Provides configuration information for connecting to an
    OpenStack Images service.
    """

    def __init__(self, conf):
        self.conf = conf

    def get(self, item_name, default_value=None):
        try:
            return self.conf.get("image", item_name)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            return default_value

    @property
    def host(self):
        """Host IP for making Images API requests. Defaults to '127.0.0.1'."""
        return self.get("host", "127.0.0.1")

    @property
    def port(self):
        """Listen port of the Images service."""
        return int(self.get("port", "9292"))

    @property
    def api_version(self):
        """Version of the API"""
        return self.get("api_version", "1")

    @property
    def username(self):
        """Username to use for Images API requests. Defaults to 'admin'."""
        return self.get("user", "admin")

    @property
    def password(self):
        """Password for user"""
        return self.get("password", "")

    @property
    def tenant(self):
        """Tenant to use for Images API requests. Defaults to 'admin'."""
        return self.get("tenant", "admin")

    @property
    def service_token(self):
        """Token to use in querying the API. Default: None"""
        return self.get("service_token")

    @property
    def auth_url(self):
        """Optional URL to auth service. Will be discovered if None"""
        return self.get("auth_url")


class TempestConfig(object):
    """Provides OpenStack configuration information."""

    DEFAULT_CONFIG_DIR = os.path.join(
        os.path.abspath(
          os.path.dirname(
            os.path.dirname(__file__))),
        "etc")

    DEFAULT_CONFIG_FILE = "tempest.conf"

    def __init__(self):
        """Initialize a configuration from a conf directory and conf file."""

        # Environment variables override defaults...
        conf_dir = os.environ.get('TEMPEST_CONFIG_DIR',
            self.DEFAULT_CONFIG_DIR)
        conf_file = os.environ.get('TEMPEST_CONFIG',
            self.DEFAULT_CONFIG_FILE)

        path = os.path.join(conf_dir, conf_file)

        if not os.path.exists(path):
            msg = "Config file %(path)s not found" % locals()
            raise RuntimeError(msg)

        self._conf = self.load_config(path)
        self.compute = ComputeConfig(self._conf)
        self.identity = IdentityConfig(self._conf)
        self.images = ImagesConfig(self._conf)

    def load_config(self, path):
        """Read configuration from given path and return a config object."""
        config = ConfigParser.SafeConfigParser()
        config.read(path)
        return config
