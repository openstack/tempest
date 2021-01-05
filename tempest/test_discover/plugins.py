# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import abc

from oslo_log import log as logging
import stevedore

from tempest.lib.common.utils import misc
from tempest.lib.services import clients

LOG = logging.getLogger(__name__)


class TempestPlugin(object, metaclass=abc.ABCMeta):
    """Provide basic hooks for an external plugin

    To provide tempest the necessary information to run the plugin.
    """

    @abc.abstractmethod
    def load_tests(self):
        """Return the information necessary to load the tests in the plugin.

        :return: a tuple with the first value being the test_dir and the second
                 being the top_level
        :rtype: tuple
        """
        return

    @abc.abstractmethod
    def register_opts(self, conf):
        """Add additional configuration options to tempest.

        This method will be run for the plugin during the register_opts()
        function in tempest.config.

        :param ConfigOpts conf: The conf object that can be used to register
            additional options on.

        Example::

            # Config options are defined in a config.py module
            service_option = cfg.BoolOpt(
                "my_service",
                default=True,
                help="Whether or not my service is available")

            # Note: as long as the group is listed in get_opt_lists,
            # it will be possible to access its optins in the plugin code
            # via ("-" in the group name are replaces with "_"):
            #     CONF.my_service.<option_name>
            my_service_group = cfg.OptGroup(name="my-service",
                                            title="My service options")

            MyServiceGroup = [<list of options>]
            # (...) More groups and options...

            # Plugin is implemented in a plugin.py module
            from my_plugin import config as my_config

            def register_opts(self, conf):
                conf.register_opt(my_config.service_option,
                                  group='service_available')
                conf.register_group(my_config.my_service_group)
                conf.register_opts(my_config.MyServiceGroup,
                                   my_config.my_service_group)

                conf.register_group(my_config.my_service_feature_group)
                conf.register_opts(my_config.MyServiceFeaturesGroup,
                                   my_config.my_service_feature_group)
        """
        return

    @abc.abstractmethod
    def get_opt_lists(self):
        """Get a list of options for sample config generation

        :return option_list: A list of tuples with the group name and options
                             in that group.
        :rtype: list

        Example::

            # Config options are defined in a config.py module
            service_option = cfg.BoolOpt(
                "my_service", default=True,
                help="Whether or not my service is available")

            my_service_group = cfg.OptGroup(name="my-service",
                                            title="My service options")
            my_service_features_group = cfg.OptGroup(
                name="my-service-features",
                title="My service available features")

            MyServiceGroup = [<list of options>]
            MyServiceFeaturesGroup = [<list of options>]

            # Plugin is implemented in a plugin.py module
            from my_plugin import config as my_config

            def get_opt_lists(self, conf):
                return [
                    (my_service_group.name, MyServiceGroup),
                    (my_service_features_group.name, MyServiceFeaturesGroup)
                ]
        """
        return []

    def get_service_clients(self):
        """Get a list of the service clients for registration

        If the plugin implements service clients for one or more APIs, it
        may return their details by this method for automatic registration
        in any ServiceClients object instantiated by tests.
        The default implementation returns an empty list.

        :returns: Each element of the list represents the service client for an
          API. Each dict must define all parameters required for the invocation
          of `service_clients.ServiceClients.register_service_client_module`.
        :rtype: list of dictionaries

        Example implementation with one service client::

            def get_service_clients(self):
                # Example implementation with one service client
                myservice_config = config.service_client_config('myservice')
                params = {
                    'name': 'myservice',
                    'service_version': 'myservice',
                    'module_path': 'myservice_tempest_tests.services',
                    'client_names': ['API1Client', 'API2Client'],
                }
                params.update(myservice_config)
                return [params]

        Example implementation with two service clients::

            def get_service_clients(self):
                # Example implementation with two service clients
                foo1_config = config.service_client_config('foo')
                params_foo1 = {
                    'name': 'foo_v1',
                    'service_version': 'foo.v1',
                    'module_path': 'bar_tempest_tests.services.foo.v1',
                    'client_names': ['API1Client', 'API2Client'],
                }
                params_foo1.update(foo_config)
                foo2_config = config.service_client_config('foo')
                params_foo2 = {
                    'name': 'foo_v2',
                    'service_version': 'foo.v2',
                    'module_path': 'bar_tempest_tests.services.foo.v2',
                    'client_names': ['API1Client', 'API2Client'],
                }
                params_foo2.update(foo2_config)
                return [params_foo1, params_foo2]
        """
        return []


@misc.singleton
class TempestTestPluginManager(object):
    """Tempest test plugin manager class

    This class is used to manage the lifecycle of external tempest test
    plugins. It provides functions for getting set
    """

    def __init__(self):
        self.ext_plugins = stevedore.ExtensionManager(
            'tempest.test_plugins', invoke_on_load=True,
            propagate_map_exceptions=True,
            on_load_failure_callback=self.failure_hook)

    @staticmethod
    def failure_hook(_, ep, err):
        LOG.error('Could not load %r: %s', ep.name, err)
        raise err

    def get_plugin_load_tests_tuple(self):
        load_tests_dict = {}
        for plug in self.ext_plugins:
            LOG.info('Loading tests from Tempest plugin: %s', plug.name)
            load_tests_dict[plug.name] = plug.obj.load_tests()
        return load_tests_dict

    def register_plugin_opts(self, conf):
        for plug in self.ext_plugins:
            LOG.info('Register additional config options from Tempest '
                     'plugin: %s', plug.name)
            try:
                plug.obj.register_opts(conf)
            except Exception:
                LOG.exception('Plugin %s raised an exception trying to run '
                              'register_opts', plug.name)

    def get_plugin_options_list(self):
        plugin_options = []
        for plug in self.ext_plugins:
            opt_list = plug.obj.get_opt_lists()
            LOG.info('List additional config options registered by '
                     'Tempest plugin: %s', plug.name)

            if opt_list:
                plugin_options.extend(opt_list)
        return plugin_options

    def _register_service_clients(self):
        registry = clients.ClientsRegistry()
        for plug in self.ext_plugins:
            try:
                service_clients = plug.obj.get_service_clients()
                if service_clients:
                    registry.register_service_client(
                        plug.name, service_clients)
            except Exception:
                LOG.exception('Plugin %s raised an exception trying to run '
                              'get_service_clients', plug.name)
