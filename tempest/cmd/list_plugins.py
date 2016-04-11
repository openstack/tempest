#!/usr/bin/env python

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Utility for listing all currently installed Tempest plugins.

**Usage:** ``tempest list-plugins``.
"""

from cliff import command
from oslo_log import log as logging
import prettytable

from tempest.test_discover.plugins import TempestTestPluginManager

LOG = logging.getLogger(__name__)


class TempestListPlugins(command.Command):
    def take_action(self, parsed_args):
        self._list_plugins()
        return 0

    def get_description(self):
        return 'List all tempest plugins'

    def _list_plugins(self):
        plugins = TempestTestPluginManager()

        output = prettytable.PrettyTable(["Name", "EntryPoint"])
        for plugin in plugins.ext_plugins.extensions:
            output.add_row([
                plugin.name, plugin.entry_point_target])

        print(output)
