from storm.services.nova.json.images_client import ImagesClient
from storm.services.nova.json.flavors_client import FlavorsClient
from storm.services.nova.json.servers_client import ServersClient
from storm.common.utils import data_utils
import storm.config


class Manager(object):

    def __init__(self):
        """
        Top level manager for all Openstack APIs
        """

        self.config = storm.config.StormConfig()
        self.auth_url = data_utils.build_url(self.config.nova.host,
                                        self.config.nova.port,
                                        self.config.nova.apiVer,
                                        self.config.nova.path)

        if self.config.env.authentication == 'keystone_v2':
            self.servers_client = ServersClient(self.config.nova.username,
                                                self.config.nova.api_key,
                                                self.auth_url,
                                                self.config.nova.tenant_name)
            self.flavors_client = FlavorsClient(self.config.nova.username,
                                                self.config.nova.api_key,
                                                self.auth_url,
                                                self.config.nova.tenant_name)
            self.images_client = ImagesClient(self.config.nova.username,
                                              self.config.nova.api_key,
                                              self.auth_url,
                                              self.config.nova.tenant_name)
        else:
            #Assuming basic/native authentication
            self.servers_client = ServersClient(self.config.nova.username,
                                                self.config.nova.api_key,
                                                self.auth_url)
            self.flavors_client = FlavorsClient(self.config.nova.username,
                                                self.config.nova.api_key,
                                                self.auth_url)
            self.images_client = ImagesClient(self.config.nova.username,
                                              self.config.nova.api_key,
                                              self.auth_url)
