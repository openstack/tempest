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

import json
import os

from oslo_log import log as logging
import yaml

import tempest.cli
from tempest import config
from tempest import test

CONF = config.CONF

LOG = logging.getLogger(__name__)


class SimpleReadOnlyHeatClientTest(tempest.cli.ClientTestBase):
    """Basic, read-only tests for Heat CLI client.

    Basic smoke test for the heat CLI commands which do not require
    creating or modifying stacks.
    """

    @classmethod
    def resource_setup(cls):
        if (not CONF.service_available.heat):
            msg = ("Skipping all Heat cli tests because it is "
                   "not available")
            raise cls.skipException(msg)
        super(SimpleReadOnlyHeatClientTest, cls).resource_setup()
        cls.heat_template_path = os.path.join(os.path.dirname(
            os.path.dirname(os.path.realpath(__file__))),
            'heat_templates/heat_minimal.yaml')

    def heat(self, *args, **kwargs):
        return self.clients.heat(
            *args, endpoint_type=CONF.orchestration.endpoint_type, **kwargs)

    @test.idempotent_id('0ae034bb-ce35-45e8-b7aa-3e339cd3140f')
    def test_heat_stack_list(self):
        self.heat('stack-list')

    @test.idempotent_id('a360d069-7250-4aed-9721-0a6f2db7c3fa')
    def test_heat_stack_list_debug(self):
        self.heat('stack-list', flags='--debug')

    @test.idempotent_id('e1b7c177-5ab4-4d3f-8a26-ea01ebbd2b8c')
    def test_heat_resource_template_fmt_default(self):
        ret = self.heat('resource-template OS::Nova::Server')
        self.assertIn('Type: OS::Nova::Server', ret)

    @test.idempotent_id('93f82f76-aab2-4910-9359-11cf48f2a46b')
    def test_heat_resource_template_fmt_arg_short_yaml(self):
        ret = self.heat('resource-template -F yaml OS::Nova::Server')
        self.assertIn('Type: OS::Nova::Server', ret)
        self.assertIsInstance(yaml.safe_load(ret), dict)

    @test.idempotent_id('7356a98c-e14d-43f0-8c25-c9f7daa0aafa')
    def test_heat_resource_template_fmt_arg_long_json(self):
        ret = self.heat('resource-template --format json OS::Nova::Server')
        self.assertIn('"Type": "OS::Nova::Server"', ret)
        self.assertIsInstance(json.loads(ret), dict)

    @test.idempotent_id('2fd99d20-beff-4667-b42e-de9095f671d7')
    def test_heat_resource_type_list(self):
        ret = self.heat('resource-type-list')
        rsrc_types = self.parser.listing(ret)
        self.assertTableStruct(rsrc_types, ['resource_type'])

    @test.idempotent_id('62f60dbf-d139-4698-b230-a09fb531d643')
    def test_heat_resource_type_show(self):
        rsrc_schema = self.heat('resource-type-show OS::Nova::Server')
        # resource-type-show returns a json resource schema
        self.assertIsInstance(json.loads(rsrc_schema), dict)

    @test.idempotent_id('6ca16ff7-9d5f-4448-a8c2-4cecc7b5ba3a')
    def test_heat_template_validate_yaml(self):
        ret = self.heat('template-validate -f %s' % self.heat_template_path)
        # On success template-validate returns a json representation
        # of the template parameters
        self.assertIsInstance(json.loads(ret), dict)

    @test.idempotent_id('35241014-16ea-4cb6-ad3e-4ee5f41446de')
    def test_heat_template_validate_hot(self):
        ret = self.heat('template-validate -f %s' % self.heat_template_path)
        self.assertIsInstance(json.loads(ret), dict)

    @test.idempotent_id('34d43e0a-36dc-4ea8-9b85-0189e3de89d8')
    def test_heat_help(self):
        self.heat('help')

    @tempest.cli.min_client_version(client='heat', version='0.2.7')
    @test.idempotent_id('c122c08b-839d-49d1-afd1-bc546b2d18d3')
    def test_heat_bash_completion(self):
        self.heat('bash-completion')

    @test.idempotent_id('1b045e12-2fa0-4895-9282-00668428dfbe')
    def test_heat_help_cmd(self):
        # Check requesting help for a specific command works
        help_text = self.heat('help resource-template')
        lines = help_text.split('\n')
        self.assertFirstLineStartsWith(lines, 'usage: heat resource-template')

    @test.idempotent_id('c7837f8f-d0a8-47fd-b75b-14ba3e3fa9a2')
    def test_heat_version(self):
        self.heat('', flags='--version')
