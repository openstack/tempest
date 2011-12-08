import os

from tempest.services.nova.json.images_client import ImagesClient
from tempest.services.nova.json.flavors_client import FlavorsClient
from tempest.services.nova.json.servers_client import ServersClient
from tempest.services.nova.json.limits_client import LimitsClient
from tempest.common.utils import data_utils
import tempest.config


class Manager(object):

    DEFAULT_CONFIG_DIR = os.path.join(
        os.path.abspath(
          os.path.dirname(
            os.path.dirname(__file__))),
        "etc")

    DEFAULT_CONFIG_FILE = "tempest.conf"

    def __init__(self):
        """
        Top level manager for all Openstack APIs
        """
        # Environment variables override defaults...
        config_dir = os.environ.get('TEMPEST_CONFIG_DIR',
            self.DEFAULT_CONFIG_DIR)
        config_file = os.environ.get('TEMPEST_CONFIG',
            self.DEFAULT_CONFIG_FILE)
        self.config = tempest.config.TempestConfig(config_dir, config_file)
        self.auth_url = data_utils.build_url(self.config.nova.host,
                                        self.config.nova.port,
                                        self.config.nova.apiVer,
                                        self.config.nova.path)

        if self.config.env.authentication == 'keystone_v2':
            self.servers_client = ServersClient(self.config,
                                                self.config.nova.username,
                                                self.config.nova.api_key,
                                                self.auth_url,
                                                self.config.nova.tenant_name)
            self.flavors_client = FlavorsClient(self.config,
                                                self.config.nova.username,
                                                self.config.nova.api_key,
                                                self.auth_url,
                                                self.config.nova.tenant_name)
            self.images_client = ImagesClient(self.config,
                                              self.config.nova.username,
                                              self.config.nova.api_key,
                                              self.auth_url,
                                              self.config.nova.tenant_name)
            self.limits_client = LimitsClient(self.config,
                                              self.config.nova.username,
                                              self.config.nova.api_key,
                                              self.auth_url,
                                              self.config.nova.tenant_name)

        else:
            #Assuming basic/native authentication
            self.servers_client = ServersClient(self.config,
                                                self.config.nova.username,
                                                self.config.nova.api_key,
                                                self.auth_url)
            self.flavors_client = FlavorsClient(self.config,
                                                self.config.nova.username,
                                                self.config.nova.api_key,
                                                self.auth_url)
            self.images_client = ImagesClient(self.config,
                                              self.config.nova.username,
                                              self.config.nova.auth_url,
                                              self.config.nova.api_key,
                                              self.auth_url)
            self.limits_client = LimitsClient(self.config,
                                              self.config.nova.username,
                                              self.config.nova.auth_url,
                                              self.config.nova.api_key,
                                              self.auth_url)
