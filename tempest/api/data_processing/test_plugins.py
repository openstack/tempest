# Copyright (c) 2014 Mirantis Inc.
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

from tempest.api.data_processing import base as dp_base
from tempest import test


class PluginsTest(dp_base.BaseDataProcessingTest):
    def _list_all_plugin_names(self):
        """Returns all enabled plugin names.

        It ensures main plugins availability.
        """
        _, plugins = self.client.list_plugins()
        plugins_names = [plugin['name'] for plugin in plugins]
        self.assertIn('vanilla', plugins_names)
        self.assertIn('hdp', plugins_names)

        return plugins_names

    @test.attr(type='smoke')
    def test_plugin_list(self):
        self._list_all_plugin_names()

    @test.attr(type='smoke')
    def test_plugin_get(self):
        for plugin_name in self._list_all_plugin_names():
            _, plugin = self.client.get_plugin(plugin_name)
            self.assertEqual(plugin_name, plugin['name'])

            for plugin_version in plugin['versions']:
                _, detailed_plugin = self.client.get_plugin(plugin_name,
                                                            plugin_version)
                self.assertEqual(plugin_name, detailed_plugin['name'])

                # check that required image tags contains name and version
                image_tags = detailed_plugin['required_image_tags']
                self.assertIn(plugin_name, image_tags)
                self.assertIn(plugin_version, image_tags)
