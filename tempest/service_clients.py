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

import copy
import importlib
import inspect
import logging

from tempest.lib import auth
from tempest.lib import exceptions
from tempest.lib.services import clients
from tempest.lib.services import compute
from tempest.lib.services import image
from tempest.lib.services import network

LOG = logging.getLogger(__name__)

client_modules_by_service_name = {
    'compute': compute,
    'image.v1': image.v1,
    'image.v2': image.v2,
    'network': network
}


def tempest_modules():
    """List of service client modules available in Tempest.

    Provides a list of service modules available Tempest.
    """
    return set(['compute', 'identity.v2', 'identity.v3', 'image.v1',
                'image.v2', 'network', 'object-storage', 'volume.v1',
                'volume.v2', 'volume.v3'])


def available_modules():
    """List of service client modules available in Tempest and plugins

    The list of available modules can be used for automatic configuration.

    :raise PluginRegistrationException: if a plugin exposes a service_version
        already defined by Tempest or another plugin.

    Examples:

        >>> from tempest import config
        >>> params = {}
        >>> for service_version in available_modules():
        >>>     service = service_version.split('.')[0]
        >>>     params[service] = config.service_client_config(service)
        >>> service_clients = ServiceClients(creds, identity_uri,
        >>>                                  client_parameters=params)
    """
    extra_service_versions = set([])
    plugin_services = clients.ClientsRegistry().get_service_clients()
    for plugin_name in plugin_services:
        plug_service_versions = set([x['service_version'] for x in
                                     plugin_services[plugin_name]])
        # If a plugin exposes a duplicate service_version raise an exception
        if plug_service_versions:
            if not plug_service_versions.isdisjoint(extra_service_versions):
                detailed_error = (
                    'Plugin %s is trying to register a service %s already '
                    'claimed by another one' % (plugin_name,
                                                extra_service_versions &
                                                plug_service_versions))
                raise exceptions.PluginRegistrationException(
                    name=plugin_name, detailed_error=detailed_error)
            if not plug_service_versions.isdisjoint(tempest_modules()):
                detailed_error = (
                    'Plugin %s is trying to register a service %s already '
                    'claimed by a Tempest one' % (plugin_name,
                                                  tempest_modules() &
                                                  plug_service_versions))
                raise exceptions.PluginRegistrationException(
                    name=plugin_name, detailed_error=detailed_error)
        extra_service_versions |= plug_service_versions
    return tempest_modules() | extra_service_versions


class ClientsFactory(object):
    """Builds service clients for a service client module

    This class implements the logic of feeding service client parameters
    to service clients from a specific module. It allows setting the
    parameters once and obtaining new instances of the clients without the
    need of passing any parameter.

    ClientsFactory can be used directly, or consumed via the `ServiceClients`
    class, which manages the authorization part.
    """

    def __init__(self, module_path, client_names, auth_provider, **kwargs):
        """Initialises the client factory

        :param module_path Path to module that includes all service clients.
            All service client classes must be exposed by a single module.
            If they are separated in different modules, defining __all__
            in the root module can help, similar to what is done by service
            clients in tempest.
        :param client_names List or set of names of the service client classes.
        :param auth_provider The auth provider used to initialise client.
        :param kwargs Parameters to be passed to all clients. Parameters values
            can be overwritten when clients are initialised, but parameters
            cannot be deleted.
        :raise ImportError if the specified module_path cannot be imported

        Example:

            >>> # Get credentials and an auth_provider
            >>> clients = ClientsFactory(
            >>>     module_path='my_service.my_service_clients',
            >>>     client_names=['ServiceClient1', 'ServiceClient2'],
            >>>     auth_provider=auth_provider,
            >>>     service='my_service',
            >>>     region='region1')
            >>> my_api_client = clients.MyApiClient()
            >>> my_api_client_region2 = clients.MyApiClient(region='region2')

        """
        # Import the module. If it's not importable, the raised exception
        # provides good enough information about what happened
        _module = importlib.import_module(module_path)
        # If any of the classes is not in the module we fail
        for class_name in client_names:
            # TODO(andreaf) This always passes all parameters to all clients.
            # In future to allow clients to specify the list of parameters
            # that they accept based out of a list of standard ones.

            # Obtain the class
            klass = self._get_class(_module, class_name)
            final_kwargs = copy.copy(kwargs)

            # Set the function as an attribute of the factory
            setattr(self, class_name, self._get_partial_class(
                klass, auth_provider, final_kwargs))

    @classmethod
    def _get_partial_class(cls, klass, auth_provider, kwargs):

        # Define a function that returns a new class instance by
        # combining default kwargs with extra ones
        def partial_class(**later_kwargs):
            kwargs.update(later_kwargs)
            return klass(auth_provider=auth_provider, **kwargs)

        return partial_class

    @classmethod
    def _get_class(cls, module, class_name):
        klass = getattr(module, class_name, None)
        if not klass:
            msg = 'Invalid class name, %s is not found in %s'
            raise AttributeError(msg % (class_name, module))
        if not inspect.isclass(klass):
            msg = 'Expected a class, got %s of type %s instead'
            raise TypeError(msg % (klass, type(klass)))
        return klass


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
        self._registered_services = set([])
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

        # Register service clients owned by tempest
        for service in tempest_modules():
            if service in list(client_modules_by_service_name):
                attribute = service.replace('.', '_')
                configs = service.split('.')[0]
                module = client_modules_by_service_name[service]
                self.register_service_client_module(
                    attribute, service, module.__name__,
                    module.__all__, **self.parameters[configs])

        # Register service clients from plugins
        clients_registry = clients.ClientsRegistry()
        plugin_service_clients = clients_registry.get_service_clients()
        for plugin in plugin_service_clients:
            service_clients = plugin_service_clients[plugin]
            # Each plugin returns a list of service client parameters
            for service_client in service_clients:
                # NOTE(andreaf) If a plugin cannot register, stop the
                # registration process, log some details to help
                # troubleshooting, and re-raise
                try:
                    self.register_service_client_module(**service_client)
                except Exception:
                    LOG.exception(
                        'Failed to register service client from plugin %s '
                        'with parameters %s' % (plugin, service_client))
                    raise

    def register_service_client_module(self, name, service_version,
                                       module_path, client_names, **kwargs):
        """Register a service client module

        Initiates a client factory for the specified module, using this
        class auth_provider, and accessible via a `name` attribute in the
        service client.

        :param name: Name used to access the client
        :param service_version: Name of the service complete with version.
            Used to track registered services. When a plugin implements it,
            it can be used by other plugins to obtain their configuration.
        :param module_path: Path to module that includes all service clients.
            All service client classes must be exposed by a single module.
            If they are separated in different modules, defining __all__
            in the root module can help, similar to what is done by service
            clients in tempest.
        :param client_names: List or set of names of service client classes.
        :param kwargs: Extra optional parameters to be passed to all clients.
            ServiceClient provides defaults for region, dscv, ca_certs and
            trace_requests.
        :raise ServiceClientRegistrationException: if the provided name is
            already in use or if service_version is already registered.
        :raise ImportError: if module_path cannot be imported.
        """
        if hasattr(self, name):
            using_name = getattr(self, name)
            detailed_error = 'Module name already in use: %s' % using_name
            raise exceptions.ServiceClientRegistrationException(
                name=name, service_version=service_version,
                module_path=module_path, client_names=client_names,
                detailed_error=detailed_error)
        if service_version in self.registered_services:
            detailed_error = 'Service %s already registered.' % service_version
            raise exceptions.ServiceClientRegistrationException(
                name=name, service_version=service_version,
                module_path=module_path, client_names=client_names,
                detailed_error=detailed_error)
        params = dict(region=self.region,
                      disable_ssl_certificate_validation=self.dscv,
                      ca_certs=self.ca_certs,
                      trace_requests=self.trace_requests)
        params.update(kwargs)
        # Instantiate the client factory
        _factory = ClientsFactory(module_path=module_path,
                                  client_names=client_names,
                                  auth_provider=self.auth_provider,
                                  **params)
        # Adds the client factory to the service_client
        setattr(self, name, _factory)
        # Add the name of the new service in self.SERVICES for discovery
        self._registered_services.add(service_version)

    @property
    def registered_services(self):
        # TODO(andreaf) Temporary set needed until all services are migrated
        _non_migrated_services = tempest_modules() - set(
            client_modules_by_service_name)
        return self._registered_services | _non_migrated_services

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
