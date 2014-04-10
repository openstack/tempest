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


class SimpleReadOnlySaharaClientTest(cli.ClientTestBase):
    """Basic, read-only tests for Sahara CLI client.

    Checks return values and output of read-only commands.
    These tests do not presume any content, nor do they create
    their own. They only verify the structure of output if present.
    """

    @classmethod
    def setUpClass(cls):
        if not CONF.service_available.sahara:
            msg = "Skipping all Sahara cli tests because it is not available"
            raise cls.skipException(msg)
        super(SimpleReadOnlySaharaClientTest, cls).setUpClass()

    @test.attr(type='negative')
    def test_sahara_fake_action(self):
        self.assertRaises(subprocess.CalledProcessError,
                          self.sahara,
                          'this-does-not-exist')

    def test_sahara_plugins_list(self):
        plugins = self.parser.listing(self.sahara('plugin-list'))
        self.assertTableStruct(plugins, [
            'name',
            'versions',
            'title'
        ])

    def test_sahara_plugins_show(self):
        result = self.sahara('plugin-show', params='--name vanilla')
        plugin = self.parser.listing(result)
        self.assertTableStruct(plugin, [
            'Property',
            'Value'
        ])

    def test_sahara_node_group_template_list(self):
        result = self.sahara('node-group-template-list')
        node_group_templates = self.parser.listing(result)
        self.assertTableStruct(node_group_templates, [
            'name',
            'id',
            'plugin_name',
            'node_processes',
            'description'
        ])

    def test_sahara_cluster_template_list(self):
        result = self.sahara('cluster-template-list')
        cluster_templates = self.parser.listing(result)
        self.assertTableStruct(cluster_templates, [
            'name',
            'id',
            'plugin_name',
            'node_groups',
            'description'
        ])

    def test_sahara_cluster_list(self):
        result = self.sahara('cluster-list')
        clusters = self.parser.listing(result)
        self.assertTableStruct(clusters, [
            'name',
            'id',
            'status',
            'node_count'
        ])

    def test_sahara_data_source_list(self):
        result = self.sahara('data-source-list')
        data_sources = self.parser.listing(result)
        self.assertTableStruct(data_sources, [
            'name',
            'id',
            'type',
            'description'
        ])

    def test_sahara_job_binary_data_list(self):
        result = self.sahara('job-binary-data-list')
        job_binary_data_list = self.parser.listing(result)
        self.assertTableStruct(job_binary_data_list, [
            'id',
            'name'
        ])

    def test_sahara_job_binary_list(self):
        result = self.sahara('job-binary-list')
        job_binaries = self.parser.listing(result)
        self.assertTableStruct(job_binaries, [
            'id',
            'name',
            'description'
        ])

    def test_sahara_job_template_list(self):
        result = self.sahara('job-template-list')
        job_templates = self.parser.listing(result)
        self.assertTableStruct(job_templates, [
            'id',
            'name',
            'description'
        ])

    def test_sahara_job_list(self):
        result = self.sahara('job-list')
        jobs = self.parser.listing(result)
        self.assertTableStruct(jobs, [
            'id',
            'cluster_id',
            'status'
        ])
