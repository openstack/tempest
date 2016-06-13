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


def tempest_modules():
    """List of service client modules available in Tempest.

    Provides a list of service modules available Tempest.
    """
    return set(['compute', 'identity.v2', 'identity.v3', 'image.v1',
                'image.v2', 'network', 'object-storage', 'volume.v1',
                'volume.v2', 'volume.v3'])


def available_modules():
    """List of service client modules available in Tempest and plugins"""
    # TODO(andreaf) For now this returns only tempest_modules
    return tempest_modules()


class ServiceClients(object):
    """Service client provider class

    The ServiceClients object provides a useful means for tests to access
    service clients configured for a specified set of credentials.
    It hides some of the complexity from the authorization and configuration
    layers.

    Examples:

        >>> from tempest import service_clients
        >>> johndoe = cred_provider.get_creds_by_role(['johndoe'])
        >>> johndoe_clients = service_clients.ServiceClients(johndoe,
        >>>                                                  identity_uri)
        >>> johndoe_servers = johndoe_clients.servers_client.list_servers()

    """
    # NOTE(andreaf) This class does not depend on tempest configuration
    # and its meant for direct consumption by external clients such as tempest
    # plugins. Tempest provides a wrapper class, `clients.Manager`, that
    # initialises this class using values from tempest CONF object. The wrapper
    # class should only be used by tests hosted in Tempest.

    def __init__(self, credentials, identity_uri, region=None, scope='project',
                 disable_ssl_certificate_validation=True, ca_certs=None,
                 trace_requests='', client_parameters=None):
        """Service Clients provider

        Instantiate a `ServiceClients` object, from a set of credentials and an
        identity URI. The identity version is inferred from the credentials
        object. Optionally auth scope can be provided.

        A few parameters can be given a value which is applied as default
        for all service clients: region, dscv, ca_certs, trace_requests.

        Parameters dscv, ca_certs and trace_requests all apply to the auth
        provider as well as any service clients provided by this manager.

        Any other client parameter must be set via client_parameters.
        The list of available parameters is defined in the service clients
        interfaces. For reference, most clients will accept 'region',
        'service', 'endpoint_type', 'build_timeout' and 'build_interval', which
        are all inherited from RestClient.

        The `config` module in Tempest exposes an helper function
        `service_client_config` that can be used to extract from configuration
        a dictionary ready to be injected in kwargs.

        Exceptions are:
        - Token clients for 'identity' have a very different interface
        - Volume client for 'volume' accepts 'default_volume_size'
        - Servers client from 'compute' accepts 'enable_instance_password'

        Examples:

            >>> identity_params = config.service_client_config('identity')
            >>> params = {
            >>>     'identity': identity_params,
            >>>     'compute': {'region': 'region2'}}
            >>> manager = lib_manager.Manager(
            >>>     my_creds, identity_uri, client_parameters=params)

        :param credentials: An instance of `auth.Credentials`
        :param identity_uri: URI of the identity API. This should be a
                             mandatory parameter, and it will so soon.
        :param region: Default value of region for service clients.
        :param scope: default scope for tokens produced by the auth provider
        :param disable_ssl_certificate_validation Applies to auth and to all
                                                  service clients.
        :param ca_certs Applies to auth and to all service clients.
        :param trace_requests Applies to auth and to all service clients.
        :param client_parameters Dictionary with parameters for service
            clients. Keys of the dictionary are the service client service
            name, as declared in `service_clients.available_modules()` except
            for the version. Values are dictionaries of parameters that are
            going to be passed to all clients in the service client module.

        Examples:

            >>> params_service_x = {'param_name': 'param_value'}
            >>> client_parameters = { 'service_x': params_service_x }

            >>> params_service_y = config.service_client_config('service_y')
            >>> client_parameters['service_y'] = params_service_y

        """
        self.credentials = credentials
        self.identity_uri = identity_uri
        if not identity_uri:
            raise exceptions.InvalidCredentials(
                'ServiceClients requires a non-empty identity_uri.')
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
        # Setup some defaults for client parameters of registered services
        client_parameters = client_parameters or {}
        self.parameters = {}
        # Parameters are provided for unversioned services
        unversioned_services = set(
            [x.split('.')[0] for x in available_modules()])
        for service in unversioned_services:
            self.parameters[service] = self._setup_parameters(
                client_parameters.pop(service, {}))
        # Check that no client parameters was supplied for unregistered clients
        if client_parameters:
            raise exceptions.UnknownServiceClient(
                services=list(client_parameters.keys()))

    def _setup_parameters(self, parameters):
        """Setup default values for client parameters

        Region by default is the region passed as an __init__ parameter.
        Checks that no parameter for an unknown service is provided.
        """
        _parameters = {}
        # Use region from __init__
        if self.region:
            _parameters['region'] = self.region
        # Update defaults with specified parameters
        _parameters.update(parameters)
        # If any parameter is left, parameters for an unknown service were
        # provided as input. Fail rather than ignore silently.
        return _parameters
