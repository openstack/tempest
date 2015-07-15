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
from tempest_lib.common.utils import misc


LOG = logging.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class TempestPlugin(object):
    """A TempestPlugin class provides the basic hooks for an external
    plugin to provide tempest the necessary information to run the plugin.
    """

    @abc.abstractmethod
    def load_tests(self):
        """Method to return the information necessary to load the tests in the
        plugin.

        :return: a tuple with the first value being the test_dir and the second
                 being the top_level
        :rtype: tuple
        """
        return


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
