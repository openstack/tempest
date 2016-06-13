# Copyright 2012 OpenStack Foundation
# Copyright (c) 2016 Hewlett-Packard Enterprise Development Company, L.P.
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

from tempest.lib import auth
from tempest.lib import exceptions


class ServiceClients(object):
    """Service client provider class

    The ServiceClients object provides a useful means for tests to access
    service clients configured for a specified set of credentials.
    It hides some of the complexity from the authorization and configuration
    layers.

    Examples:

        >>> from tempest import service_clients
        >>> johndoe = cred_provider.get_creds_by_role(['johndoe'])
        >>> johndoe_clients = service_clients.ServiceClients(johndoe)
        >>> johndoe_servers = johndoe_clients.servers_client.list_servers()

    """
    # NOTE(andreaf) This class does not depend on tempest configuration
    # and its meant for direct consumption by external clients such as tempest
    # plugins. Tempest provides a wrapper class, `clients.Manager`, that
    # initialises this class using values from tempest CONF object. The wrapper
    # class should only be used by tests hosted in Tempest.

    def __init__(self, credentials, identity_uri, region=None,
                 scope='project', disable_ssl_certificate_validation=True,
                 ca_certs=None, trace_requests=''):
        """Service Clients provider

        Instantiate a `ServiceClients` object, from a set of credentials and an
        identity URI. The identity version is inferred from the credentials
        object. Optionally auth scope can be provided.
        Parameters dscv, ca_certs and trace_requests all apply to the auth
        provider as well as any service clients provided by this manager.

        :param credentials: An instance of `auth.Credentials`
        :param identity_uri: URI of the identity API. This should be a
                             mandatory parameter, and it will so soon.
        :param region: Default value of region for service clients.
        :param scope: default scope for tokens produced by the auth provider
        :param disable_ssl_certificate_validation Applies to auth and to all
                                                  service clients.
        :param ca_certs Applies to auth and to all service clients.
        :param trace_requests Applies to auth and to all service clients.
        """
        self.credentials = credentials
        self.identity_uri = identity_uri
        if not identity_uri:
            raise exceptions.InvalidCredentials(
                'Manager requires a non-empty identity_uri.')
        self.region = region
        # Check if passed or default credentials are valid
        if not self.credentials.is_valid():
            raise exceptions.InvalidCredentials()
        # Get the identity classes matching the provided credentials
        # TODO(andreaf) Define a new interface in Credentials to get
        # the API version from an instance
        identity = [(k, auth.IDENTITY_VERSION[k][1]) for k in
                    auth.IDENTITY_VERSION.keys() if
                    isinstance(self.credentials, auth.IDENTITY_VERSION[k][0])]
        # Zero matches or more than one are both not valid.
        if len(identity) != 1:
            raise exceptions.InvalidCredentials()
        self.auth_version, auth_provider_class = identity[0]
        self.dscv = disable_ssl_certificate_validation
        self.ca_certs = ca_certs
        self.trace_requests = trace_requests
        # Creates an auth provider for the credentials
        self.auth_provider = auth_provider_class(
            self.credentials, self.identity_uri, scope=scope,
            disable_ssl_certificate_validation=self.dscv,
            ca_certs=self.ca_certs, trace_requests=self.trace_requests)
