import tempest.config
from tempest.services.image import service as image_service
from tempest.services.nova.json.images_client import ImagesClient
from tempest.services.nova.json.flavors_client import FlavorsClient
from tempest.services.nova.json.servers_client import ServersClient
from tempest.services.nova.json.limits_client import LimitsClient
from tempest.services.nova.json.extensions_client import ExtensionsClient
from tempest.services.nova.json.security_groups_client \
import SecurityGroupsClient
from tempest.services.nova.json.floating_ips_client import FloatingIPsClient

from tempest.services.nova.json.keypairs_client import KeyPairsClient


class Manager(object):

    def __init__(self):
        """
        Top level manager for all Openstack APIs
        """
        self.config = tempest.config.TempestConfig()

        if self.config.env.authentication == 'keystone_v2':
            self.servers_client = ServersClient(self.config,
                                                self.config.nova.username,
                                                self.config.nova.api_key,
                                                self.config.nova.auth_url,
                                                self.config.nova.tenant_name)
            self.flavors_client = FlavorsClient(self.config,
                                                self.config.nova.username,
                                                self.config.nova.api_key,
                                                self.config.nova.auth_url,
                                                self.config.nova.tenant_name)
            self.images_client = ImagesClient(self.config,
                                              self.config.nova.username,
                                              self.config.nova.api_key,
                                              self.config.nova.auth_url,
                                              self.config.nova.tenant_name)
            self.limits_client = LimitsClient(self.config,
                                              self.config.nova.username,
                                              self.config.nova.api_key,
                                              self.config.nova.auth_url,
                                              self.config.nova.tenant_name)
            self.extensions_client = ExtensionsClient(self.config,
                                              self.config.nova.username,
                                              self.config.nova.api_key,
                                              self.config.nova.auth_url,
                                              self.config.nova.tenant_name)
            self.keypairs_client = KeyPairsClient(self.config,
                                              self.config.nova.username,
                                              self.config.nova.api_key,
                                              self.config.nova.auth_url,
                                              self.config.nova.tenant_name)
            self.security_groups_client = SecurityGroupsClient(self.config,
                                              self.config.nova.username,
                                              self.config.nova.api_key,
                                              self.config.nova.auth_url,
                                              self.config.nova.tenant_name)
            self.floating_ips_client = FloatingIPsClient(self.config,
                                              self.config.nova.username,
                                              self.config.nova.api_key,
                                              self.config.nova.auth_url,
                                              self.config.nova.tenant_name)
        else:
            #Assuming basic/native authentication
            self.servers_client = ServersClient(self.config,
                                                self.config.nova.username,
                                                self.config.nova.api_key,
                                                self.config.nova.auth_url)
            self.flavors_client = FlavorsClient(self.config,
                                                self.config.nova.username,
                                                self.config.nova.api_key,
                                                self.config.nova.auth_url)
            self.images_client = ImagesClient(self.config,
                                              self.config.nova.username,
                                              self.config.nova.api_key,
                                              self.config.nova.auth_url)
            self.limits_client = LimitsClient(self.config,
                                              self.config.nova.username,
                                              self.config.nova.api_key,
                                              self.config.nova.auth_url)
            self.extensions_client = ExtensionsClient(self.config,
                                              self.config.nova.username,
                                              self.config.nova.api_key,
                                              self.config.nova.auth_url)
            self.security_groups_client = SecurityGroupsClient(self.config,
                                              self.config.nova.username,
                                              self.config.nova.api_key,
                                              self.config.nova.auth_url)
            self.keypairs_client = KeyPairsClient(self.config,
                                              self.config.nova.username,
                                              self.config.nova.api_key,
                                              self.config.nova.auth_url)
            self.floating_ips_client = FloatingIPsClient(self.config,
                                              self.config.nova.username,
                                              self.config.nova.api_key,
                                              self.config.nova.auth_url)


class ServiceManager(object):

    """
    Top-level object housing clients for OpenStack APIs
    """

    def __init__(self):
        self.config = tempest.config.TempestConfig()
        self.services = {}
        self.services['image'] = image_service.Service(self.config)
        self.images = self.services['image']
