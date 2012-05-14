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

import tempest.config
from tempest import exceptions
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
from tempest.services.nova.json.volumes_client import VolumesClient
from tempest.services.identity.json.admin_client import AdminClient
from tempest.services.identity.json.admin_client import TokenClient

LOG = logging.getLogger(__name__)


class Manager(object):

    """
    Top level manager for OpenStack Compute clients
    """

    def __init__(self, username=None, password=None, tenant_name=None):
        """
        We allow overriding of the credentials used within the various
        client classes managed by the Manager object. Left as None, the
        standard username/password/tenant_name is used.

        :param username: Override of the username
        :param password: Override of the password
        :param tenant_name: Override of the tenant name
        """
        self.config = tempest.config.TempestConfig()

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

        self.servers_client = ServersClient(*client_args)
        self.flavors_client = FlavorsClient(*client_args)
        self.images_client = ImagesClient(*client_args)
        self.limits_client = LimitsClient(*client_args)
        self.extensions_client = ExtensionsClient(*client_args)
        self.keypairs_client = KeyPairsClient(*client_args)
        self.security_groups_client = SecurityGroupsClient(*client_args)
        self.floating_ips_client = FloatingIPsClient(*client_args)
        self.volumes_client = VolumesClient(*client_args)
        self.admin_client = AdminClient(*client_args)
        self.token_client = TokenClient(self.config)


class AltManager(Manager):

    """
    Manager object that uses the alt_XXX credentials for its
    managed client objects
    """

    def __init__(self):
        conf = tempest.config.TempestConfig()
        super(AltManager, self).__init__(conf.compute.alt_username,
                                         conf.compute.alt_password,
                                         conf.compute.alt_tenant_name)


class AdminManager(Manager):

    """
    Manager object that uses the alt_XXX credentials for its
    managed client objects
    """

    def __init__(self):
        conf = tempest.config.TempestConfig()
        super(AdminManager, self).__init__(conf.compute_admin.username,
                                           conf.compute_admin.password,
                                           conf.compute_admin.tenant_name)
        # TODO(jaypipes): Add Admin-Only client class construction below...


class ServiceManager(object):

    """
    Top-level object housing clients for OpenStack APIs
    """

    def __init__(self):
        self.config = tempest.config.TempestConfig()
        self.services = {}
        self.services['image'] = image_service.Service(self.config)
        self.images = self.services['image']
