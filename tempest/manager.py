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

# Default client libs
import novaclient.client
import glance.client

import tempest.config
from tempest import exceptions
# Tempest REST Fuzz testing client libs
from tempest.services.network.json import network_client
from tempest.services.nova.json import images_client
from tempest.services.nova.json import flavors_client
from tempest.services.nova.json import servers_client
from tempest.services.nova.json import limits_client
from tempest.services.nova.json import extensions_client
from tempest.services.nova.json import security_groups_client
from tempest.services.nova.json import floating_ips_client
from tempest.services.nova.json import keypairs_client
from tempest.services.nova.json import volumes_client
from tempest.services.nova.json import console_output_client

NetworkClient = network_client.NetworkClient
ImagesClient = images_client.ImagesClient
FlavorsClient = flavors_client.FlavorsClient
ServersClient = servers_client.ServersClient
LimitsClient = limits_client.LimitsClient
ExtensionsClient = extensions_client.ExtensionsClient
SecurityGroupsClient = security_groups_client.SecurityGroupsClient
FloatingIPsClient = floating_ips_client.FloatingIPsClient
KeyPairsClient = keypairs_client.KeyPairsClient
VolumesClient = volumes_client.VolumesClient
ConsoleOutputsClient = console_output_client.ConsoleOutputsClient

LOG = logging.getLogger(__name__)


class Manager(object):

    """
    Base manager class

    Manager objects are responsible for providing a configuration object
    and a client object for a test case to use in performing actions.
    """

    def __init__(self):
        self.config = tempest.config.TempestConfig()
        self.client = None


class DefaultClientManager(Manager):

    """
    Manager class that indicates the client provided by the manager
    is the default Python client that an OpenStack API provides.
    """
    pass


class FuzzClientManager(Manager):

    """
    Manager class that indicates the client provided by the manager
    is a fuzz-testing client that Tempest contains. These fuzz-testing
    clients are used to be able to throw random or invalid data at
    an endpoint and check for appropriate error messages returned
    from the endpoint.
    """
    pass


class ComputeDefaultClientManager(DefaultClientManager):

    """
    Manager that provides the default python-novaclient client object
    to access the OpenStack Compute API.
    """

    NOVACLIENT_VERSION = '2'

    def __init__(self):
        super(ComputeDefaultClientManager, self).__init__()
        username = self.config.compute.username
        password = self.config.compute.password
        tenant_name = self.config.compute.tenant_name

        if None in (username, password, tenant_name):
            msg = ("Missing required credentials. "
                   "username: %(username)s, password: %(password)s, "
                   "tenant_name: %(tenant_name)s") % locals()
            raise exceptions.InvalidConfiguration(msg)

        # Novaclient adds a /tokens/ part to the auth URL automatically
        auth_url = self.config.identity.auth_url.rstrip('tokens')

        client_args = (username, password, tenant_name, auth_url)

        # Create our default Nova client to use in testing
        self.client = novaclient.client.Client(self.NOVACLIENT_VERSION,
                        *client_args,
                        service_type=self.config.compute.catalog_type,
                        no_cache=True)


class GlanceDefaultClientManager(DefaultClientManager):
    """
    Manager that provides the default glance client object to access
    the OpenStack Images API
    """
    def __init__(self):
        super(GlanceDefaultClientManager, self).__init__()
        host = self.config.images.host
        port = self.config.images.port
        strategy = self.config.identity.strategy
        auth_url = self.config.identity.auth_url
        username = self.config.images.username
        password = self.config.images.password
        tenant_name = self.config.images.tenant_name

        if None in (host, port, username, password, tenant_name):
            msg = ("Missing required credentials. "
                    "host:%(host)s, port: %(port)s username: %(username)s, "
                    "password: %(password)s, "
                    "tenant_name: %(tenant_name)s") % locals()
            raise exceptions.InvalidConfiguration(msg)
        auth_url = self.config.identity.auth_url.rstrip('tokens')

        creds = {'strategy': strategy,
                 'username': username,
                 'password': password,
                 'tenant': tenant_name,
                 'auth_url': auth_url}

        # Create our default Glance client to use in testing
        self.client = glance.client.Client(host, port, creds=creds)


class ComputeFuzzClientManager(FuzzClientManager):

    """
    Manager that uses the Tempest REST client that can send
    random or invalid data at the OpenStack Compute API
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
        super(ComputeFuzzClientManager, self).__init__()

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

        self.servers_client = ServersClient(*client_args)
        self.flavors_client = FlavorsClient(*client_args)
        self.images_client = ImagesClient(*client_args)
        self.limits_client = LimitsClient(*client_args)
        self.extensions_client = ExtensionsClient(*client_args)
        self.keypairs_client = KeyPairsClient(*client_args)
        self.security_groups_client = SecurityGroupsClient(*client_args)
        self.floating_ips_client = FloatingIPsClient(*client_args)
        self.volumes_client = VolumesClient(*client_args)
        self.console_outputs_client = ConsoleOutputsClient(*client_args)
        self.network_client = NetworkClient(*client_args)


class ComputeFuzzClientAltManager(Manager):

    """
    Manager object that uses the alt_XXX credentials for its
    managed client objects
    """

    def __init__(self):
        conf = tempest.config.TempestConfig()
        super(ComputeFuzzClientAltManager, self).__init__(
                conf.compute.alt_username,
                conf.compute.alt_password,
                conf.compute.alt_tenant_name)


class ComputeFuzzClientAdminManager(Manager):

    """
    Manager object that uses the alt_XXX credentials for its
    managed client objects
    """

    def __init__(self):
        conf = tempest.config.TempestConfig()
        super(ComputeFuzzClientAdminManager, self).__init__(
                conf.compute_admin.username,
                conf.compute_admin.password,
                conf.compute_admin.tenant_name)
