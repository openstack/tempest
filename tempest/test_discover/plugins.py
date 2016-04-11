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
import logging

import six
import stevedore

from tempest.lib.common.utils import misc

LOG = logging.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class TempestPlugin(object):
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
        function in tempest.config

        :param ConfigOpts conf: The conf object that can be used to register
            additional options on.
        """
        return

    @abc.abstractmethod
    def get_opt_lists(self):
        """Get a list of options for sample config generation

        :return option_list: A list of tuples with the group name and options
                             in that group.
        :rtype: list
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
            load_tests_dict[plug.name] = plug.obj.load_tests()
        return load_tests_dict

    def register_plugin_opts(self, conf):
        for plug in self.ext_plugins:
            try:
                plug.obj.register_opts(conf)
            except Exception:
                LOG.exception('Plugin %s raised an exception trying to run '
                              'register_opts' % plug.name)

    def get_plugin_options_list(self):
        plugin_options = []
        for plug in self.ext_plugins:
            opt_list = plug.obj.get_opt_lists()
            if opt_list:
                plugin_options.extend(opt_list)
        return plugin_options
