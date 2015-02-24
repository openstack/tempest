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
from tempest import config
from tempest import test

CONF = config.CONF


class PluginsTest(dp_base.BaseDataProcessingTest):
    def _list_all_plugin_names(self):
        """Returns all enabled plugin names.

        It ensures main plugins availability.
        """
        plugins = self.client.list_plugins()
        plugins_names = [plugin['name'] for plugin in plugins]
        for enabled_plugin in CONF.data_processing_feature_enabled.plugins:
            self.assertIn(enabled_plugin, plugins_names)

        return plugins_names

    @test.attr(type='smoke')
    @test.idempotent_id('01a005a3-426c-4c0b-9617-d09475403e09')
    def test_plugin_list(self):
        self._list_all_plugin_names()

    @test.attr(type='smoke')
    @test.idempotent_id('53cf6487-2cfb-4a6f-8671-97c542c6e901')
    def test_plugin_get(self):
        for plugin_name in self._list_all_plugin_names():
            plugin = self.client.get_plugin(plugin_name)
            self.assertEqual(plugin_name, plugin['name'])

            for plugin_version in plugin['versions']:
                detailed_plugin = self.client.get_plugin(plugin_name,
                                                         plugin_version)
                self.assertEqual(plugin_name, detailed_plugin['name'])

                # check that required image tags contains name and version
                image_tags = detailed_plugin['required_image_tags']
                self.assertIn(plugin_name, image_tags)
                self.assertIn(plugin_version, image_tags)
