# Copyright (c) 2013 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import subprocess

from tempest import cli
from tempest import config
from tempest import test

CONF = config.CONF

LOG = logging.getLogger(__name__)


class SimpleReadOnlySavannaClientTest(cli.ClientTestBase):
    """Basic, read-only tests for Savanna CLI client.

    Checks return values and output of read-only commands.
    These tests do not presume any content, nor do they create
    their own. They only verify the structure of output if present.
    """

    @classmethod
    def setUpClass(cls):
        if not CONF.service_available.savanna:
            msg = "Skipping all Savanna cli tests because it is not available"
            raise cls.skipException(msg)
        super(SimpleReadOnlySavannaClientTest, cls).setUpClass()

    @test.attr(type='negative')
    def test_savanna_fake_action(self):
        self.assertRaises(subprocess.CalledProcessError,
                          self.savanna,
                          'this-does-not-exist')

    def test_savanna_plugins_list(self):
        plugins = self.parser.listing(self.savanna('plugin-list'))
        self.assertTableStruct(plugins, ['name', 'versions', 'title'])

    def test_savanna_plugins_show(self):
        plugin = self.parser.listing(self.savanna('plugin-show',
                                                  params='--name vanilla'))
        self.assertTableStruct(plugin, ['Property', 'Value'])

    def test_savanna_node_group_template_list(self):
        plugins = self.parser.listing(self.savanna('node-group-template-list'))
        self.assertTableStruct(plugins, ['name', 'id', 'plugin_name',
                                         'node_processes', 'description'])

    def test_savanna_cluster_template_list(self):
        plugins = self.parser.listing(self.savanna('cluster-template-list'))
        self.assertTableStruct(plugins, ['name', 'id', 'plugin_name',
                                         'node_groups', 'description'])

    def test_savanna_cluster_list(self):
        plugins = self.parser.listing(self.savanna('cluster-list'))
        self.assertTableStruct(plugins, ['name', 'id', 'status', 'node_count'])
