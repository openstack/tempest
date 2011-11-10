from storm.services.nova.json.images_client import ImagesClient
from storm.services.nova.json.flavors_client import FlavorsClient
from storm.services.nova.json.servers_client import ServersClient
import storm.config


class Manager(object):

    def __init__(self):
        """
        Top level manager for all Openstack APIs
        """

        self.config = storm.config.StormConfig()
        if self.config.env.authentication == 'keystone_v2':
            self.servers_client = ServersClient(self.config.nova.username,
                                                self.config.nova.api_key,
                                                self.config.nova.auth_url,
                                                self.config.nova.tenant_name)
            self.flavors_client = FlavorsClient(self.config.nova.username,
                                                self.config.nova.api_key,
                                                self.config.nova.auth_url,
                                                self.config.nova.tenant_name)
            self.images_client = ImagesClient(self.config.nova.username,
                                              self.config.nova.api_key,
                                              self.config.nova.auth_url,
                                              self.config.nova.tenant_name)
        else:
            #Assuming basic/native authentication
            self.servers_client = ServersClient(self.config.nova.username,
                                                self.config.nova.api_key,
                                                self.config.nova.auth_url)
            self.flavors_client = FlavorsClient(self.config.nova.username,
                                                self.config.nova.api_key,
                                                self.config.nova.auth_url)
            self.images_client = ImagesClient(self.config.nova.username,
                                              self.config.nova.api_key,
                                              self.config.nova.auth_url)
