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
import re

from tempest_lib import exceptions
import testtools

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
    def resource_setup(cls):
        if not CONF.service_available.sahara:
            msg = "Skipping all Sahara cli tests because it is not available"
            raise cls.skipException(msg)
        super(SimpleReadOnlySaharaClientTest, cls).resource_setup()

    def sahara(self, *args, **kwargs):
        return self.clients.sahara(
            *args, endpoint_type=CONF.data_processing.endpoint_type, **kwargs)

    @test.attr(type='negative')
    @test.idempotent_id('c8809259-710f-43f9-b452-54b2be3115a9')
    def test_sahara_fake_action(self):
        self.assertRaises(exceptions.CommandFailed,
                          self.sahara,
                          'this-does-not-exist')

    @test.idempotent_id('39afe90c-0fd8-456e-89e2-da6de9680fff')
    def test_sahara_plugins_list(self):
        plugins = self.parser.listing(self.sahara('plugin-list'))
        self.assertTableStruct(plugins, [
            'name',
            'versions',
            'title'
        ])

    @test.idempotent_id('3eb36fd8-bb06-4004-9e90-84ddf4dbcf5b')
    @testtools.skipUnless(CONF.data_processing_feature_enabled.plugins,
                          'No plugins defined')
    def test_sahara_plugins_show(self):
        name_param = '--name %s' % \
            (CONF.data_processing_feature_enabled.plugins[0])
        result = self.sahara('plugin-show', params=name_param)
        plugin = self.parser.listing(result)
        self.assertTableStruct(plugin, [
            'Property',
            'Value'
        ])

    @test.idempotent_id('502b684b-3d41-4619-aa6c-4db3465ae79d')
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

    @test.idempotent_id('6c36fe4d-3b88-4b0d-b702-2a051db7dae7')
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

    @test.idempotent_id('b951949d-b9a6-49db-add5-8a18ac533810')
    def test_sahara_cluster_list(self):
        result = self.sahara('cluster-list')
        clusters = self.parser.listing(result)
        self.assertTableStruct(clusters, [
            'name',
            'id',
            'status',
            'node_count'
        ])

    @test.idempotent_id('dbc83a8c-15b6-4aa8-b274-5896577397e1')
    def test_sahara_data_source_list(self):
        result = self.sahara('data-source-list')
        data_sources = self.parser.listing(result)
        self.assertTableStruct(data_sources, [
            'name',
            'id',
            'type',
            'description'
        ])

    @test.idempotent_id('a8f77e05-d4bf-45c3-8245-57835d0de37b')
    def test_sahara_job_binary_data_list(self):
        result = self.sahara('job-binary-data-list')
        job_binary_data_list = self.parser.listing(result)
        self.assertTableStruct(job_binary_data_list, [
            'id',
            'name'
        ])

    @test.idempotent_id('a8f4d0f3-fa1c-49ce-b73f-d624d89dc381')
    def test_sahara_job_binary_list(self):
        result = self.sahara('job-binary-list')
        job_binaries = self.parser.listing(result)
        self.assertTableStruct(job_binaries, [
            'id',
            'name',
            'description'
        ])

    @test.idempotent_id('91164ca4-d049-49e0-a52a-686b408196ff')
    def test_sahara_job_template_list(self):
        result = self.sahara('job-template-list')
        job_templates = self.parser.listing(result)
        self.assertTableStruct(job_templates, [
            'id',
            'name',
            'description'
        ])

    @test.idempotent_id('6829c251-a8b6-449d-af86-7dd98b69a7ce')
    def test_sahara_job_list(self):
        result = self.sahara('job-list')
        jobs = self.parser.listing(result)
        self.assertTableStruct(jobs, [
            'id',
            'cluster_id',
            'status'
        ])

    @test.idempotent_id('e4bd5d3b-474b-4b7a-82ab-f6bb0bc89faf')
    def test_sahara_bash_completion(self):
        self.sahara('bash-completion')

    # Optional arguments
    @test.idempotent_id('699c14e5-632e-46b8-91e5-6bff8c8307e5')
    def test_sahara_help(self):
        help_text = self.sahara('help')
        lines = help_text.split('\n')
        self.assertFirstLineStartsWith(lines, 'usage: sahara')

        commands = []
        cmds_start = lines.index('Positional arguments:')
        cmds_end = lines.index('Optional arguments:')
        command_pattern = re.compile('^ {4}([a-z0-9\-\_]+)')
        for line in lines[cmds_start:cmds_end]:
            match = command_pattern.match(line)
            if match:
                commands.append(match.group(1))
        commands = set(commands)
        wanted_commands = set(('cluster-create', 'data-source-create',
                               'image-unregister', 'job-binary-create',
                               'plugin-list', 'job-binary-create', 'help'))
        self.assertFalse(wanted_commands - commands)

    @test.idempotent_id('84a18ea6-6379-4024-af6b-0e938f60dfc2')
    def test_sahara_version(self):
        version = self.sahara('', flags='--version')
        self.assertTrue(re.search('[0-9.]+', version))
