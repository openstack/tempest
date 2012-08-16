# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import logging

from tempest import config
from tempest import exceptions
from tempest.services.image import service as image_service
from tempest.services.network.json.network_client import NetworkClient
from tempest.services.nova.json.images_client import ImagesClient
from tempest.services.nova.json.flavors_client import FlavorsClient
from tempest.services.nova.json.limits_client import LimitsClientJSON
from tempest.services.nova.json.servers_client import ServersClientJSON
from tempest.services.nova.json.extensions_client import ExtensionsClient
from tempest.services.nova.json.security_groups_client \
import SecurityGroupsClient
from tempest.services.nova.json.floating_ips_client import FloatingIPsClient
from tempest.services.nova.json.keypairs_client import KeyPairsClient
from tempest.services.nova.json.volumes_client import VolumesClient
from tempest.services.nova.json.console_output_client \
import ConsoleOutputsClient
from tempest.services.nova.xml.limits_client import LimitsClientXML
from tempest.services.nova.xml.servers_client import ServersClientXML

LOG = logging.getLogger(__name__)

SERVERS_CLIENTS = {
    "json": ServersClientJSON,
    "xml": ServersClientXML,
}

LIMITS_CLIENTS = {
    "json": LimitsClientJSON,
    "xml": LimitsClientXML,
}


class Manager(object):

    """
    Top level manager for OpenStack Compute clients
    """

    def __init__(self, username=None, password=None, tenant_name=None,
                 interface='json'):
        """
        We allow overriding of the credentials used within the various
        client classes managed by the Manager object. Left as None, the
        standard username/password/tenant_name is used.

        :param username: Override of the username
        :param password: Override of the password
        :param tenant_name: Override of the tenant name
        """
        self.config = config.TempestConfig()

        # If no creds are provided, we fall back on the defaults
        # in the config file for the Compute API.
        username = username or self.config.compute.username
        password = password or self.config.compute.password
        tenant_name = tenant_name or self.config.compute.tenant_name

        if None in (username, password, tenant_name):
            msg = ("Missing required credentials. "
                   "username: %(username)s, password: %(password)s, "
                   "tenant_name: %(tenant_name)s") % locals()
            raise exceptions.InvalidConfiguration(msg)

        auth_url = self.config.identity.auth_url

        if self.config.identity.strategy == 'keystone':
            client_args = (self.config, username, password, auth_url,
                           tenant_name)
        else:
            client_args = (self.config, username, password, auth_url)

        try:
            self.servers_client = SERVERS_CLIENTS[interface](*client_args)
            self.limits_client = LIMITS_CLIENTS[interface](*client_args)
        except KeyError:
            msg = "Unsupported interface type `%s'" % interface
            raise exceptions.InvalidConfiguration(msg)
        self.flavors_client = FlavorsClient(*client_args)
        self.images_client = ImagesClient(*client_args)
        self.extensions_client = ExtensionsClient(*client_args)
        self.keypairs_client = KeyPairsClient(*client_args)
        self.security_groups_client = SecurityGroupsClient(*client_args)
        self.floating_ips_client = FloatingIPsClient(*client_args)
        self.volumes_client = VolumesClient(*client_args)
        self.console_outputs_client = ConsoleOutputsClient(*client_args)
        self.network_client = NetworkClient(*client_args)


class AltManager(Manager):

    """
    Manager object that uses the alt_XXX credentials for its
    managed client objects
    """

    def __init__(self):
        conf = config.TempestConfig()
        super(AltManager, self).__init__(conf.compute.alt_username,
                                         conf.compute.alt_password,
                                         conf.compute.alt_tenant_name)


class AdminManager(Manager):

    """
    Manager object that uses the alt_XXX credentials for its
    managed client objects
    """

    def __init__(self):
        conf = config.TempestConfig()
        super(AdminManager, self).__init__(conf.compute_admin.username,
                                           conf.compute_admin.password,
                                           conf.compute_admin.tenant_name)


class ServiceManager(object):

    """
    Top-level object housing clients for OpenStack APIs
    """

    def __init__(self):
        self.config = config.TempestConfig()
        self.services = {}
        self.services['image'] = image_service.Service(self.config)
        self.images = self.services['image']
