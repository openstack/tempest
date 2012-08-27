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
from tempest.services.nova.json.extensions_client import ExtensionsClientJSON
from tempest.services.nova.json.flavors_client import FlavorsClientJSON
from tempest.services.nova.json.floating_ips_client import \
FloatingIPsClientJSON
from tempest.services.nova.json.images_client import ImagesClientJSON
from tempest.services.nova.json.limits_client import LimitsClientJSON
from tempest.services.nova.json.servers_client import ServersClientJSON
from tempest.services.nova.json.security_groups_client \
import SecurityGroupsClient
from tempest.services.nova.json.keypairs_client import KeyPairsClientJSON
from tempest.services.nova.json.volumes_extensions_client \
import VolumesExtensionsClientJSON
from tempest.services.nova.json.console_output_client \
import ConsoleOutputsClient
from tempest.services.nova.xml.extensions_client import ExtensionsClientXML
from tempest.services.nova.xml.flavors_client import FlavorsClientXML
from tempest.services.nova.xml.floating_ips_client import \
FloatingIPsClientXML
from tempest.services.nova.xml.images_client import ImagesClientXML
from tempest.services.nova.xml.keypairs_client import KeyPairsClientXML
from tempest.services.nova.xml.limits_client import LimitsClientXML
from tempest.services.nova.xml.servers_client import ServersClientXML
from tempest.services.nova.xml.volumes_extensions_client \
import VolumesExtensionsClientXML
from tempest.services.volume.json.volumes_client import VolumesClient

LOG = logging.getLogger(__name__)

IMAGES_CLIENTS = {
    "json": ImagesClientJSON,
    "xml": ImagesClientXML,
}

KEYPAIRS_CLIENTS = {
    "json": KeyPairsClientJSON,
    "xml": KeyPairsClientXML,
}

SERVERS_CLIENTS = {
    "json": ServersClientJSON,
    "xml": ServersClientXML,
}

LIMITS_CLIENTS = {
    "json": LimitsClientJSON,
    "xml": LimitsClientXML,
}

FLAVORS_CLIENTS = {
    "json": FlavorsClientJSON,
    "xml": FlavorsClientXML
}

EXTENSIONS_CLIENTS = {
    "json": ExtensionsClientJSON,
    "xml": ExtensionsClientXML
}

VOLUMES_EXTENSIONS_CLIENTS = {
    "json": VolumesExtensionsClientJSON,
    "xml": VolumesExtensionsClientXML,
}

FLOAT_CLIENTS = {
    "json": FloatingIPsClientJSON,
    "xml": FloatingIPsClientXML,
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
        self.username = username or self.config.compute.username
        self.password = password or self.config.compute.password
        self.tenant_name = tenant_name or self.config.compute.tenant_name

        if None in (self.username, self.password, self.tenant_name):
            msg = ("Missing required credentials. "
                   "username: %(username)s, password: %(password)s, "
                   "tenant_name: %(tenant_name)s") % locals()
            raise exceptions.InvalidConfiguration(msg)

        self.auth_url = self.config.identity.auth_url

        if self.config.identity.strategy == 'keystone':
            client_args = (self.config, self.username, self.password,
                           self.auth_url, self.tenant_name)
        else:
            client_args = (self.config, self.username, self.password,
                           self.auth_url)

        try:
            self.servers_client = SERVERS_CLIENTS[interface](*client_args)
            self.limits_client = LIMITS_CLIENTS[interface](*client_args)
            self.images_client = IMAGES_CLIENTS[interface](*client_args)
            self.keypairs_client = KEYPAIRS_CLIENTS[interface](*client_args)
            self.flavors_client = FLAVORS_CLIENTS[interface](*client_args)
            self.extensions_client = \
                    EXTENSIONS_CLIENTS[interface](*client_args)
            self.volumes_extensions_client = \
                    VOLUMES_EXTENSIONS_CLIENTS[interface](*client_args)
            self.floating_ips_client = FLOAT_CLIENTS[interface](*client_args)
        except KeyError:
            msg = "Unsupported interface type `%s'" % interface
            raise exceptions.InvalidConfiguration(msg)
        self.security_groups_client = SecurityGroupsClient(*client_args)
        self.console_outputs_client = ConsoleOutputsClient(*client_args)
        self.network_client = NetworkClient(*client_args)
        self.volumes_client = VolumesClient(*client_args)


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

    def __init__(self, interface='json'):
        conf = config.TempestConfig()
        super(AdminManager, self).__init__(conf.compute_admin.username,
                                           conf.compute_admin.password,
                                           conf.compute_admin.tenant_name,
                                           interface=interface)


class ServiceManager(object):

    """
    Top-level object housing clients for OpenStack APIs
    """

    def __init__(self):
        self.config = config.TempestConfig()
        self.services = {}
        self.services['image'] = image_service.Service(self.config)
        self.images = self.services['image']
