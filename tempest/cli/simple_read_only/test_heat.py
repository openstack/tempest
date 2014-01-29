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
import yaml

import tempest.cli
from tempest import config
from tempest.openstack.common import log as logging

CONF = config.CONF

LOG = logging.getLogger(__name__)


class SimpleReadOnlyHeatClientTest(tempest.cli.ClientTestBase):
    """Basic, read-only tests for Heat CLI client.

    Basic smoke test for the heat CLI commands which do not require
    creating or modifying stacks.
    """

    @classmethod
    def setUpClass(cls):
        if (not CONF.service_available.heat):
            msg = ("Skipping all Heat cli tests because it is "
                   "not available")
            raise cls.skipException(msg)
        super(SimpleReadOnlyHeatClientTest, cls).setUpClass()

    def test_heat_stack_list(self):
        self.heat('stack-list')

    def test_heat_stack_list_debug(self):
        self.heat('stack-list', flags='--debug')

    def test_heat_resource_template_fmt_default(self):
        ret = self.heat('resource-template OS::Nova::Server')
        self.assertIn('Type: OS::Nova::Server', ret)

    def test_heat_resource_template_fmt_arg_short_yaml(self):
        ret = self.heat('resource-template -F yaml OS::Nova::Server')
        self.assertIn('Type: OS::Nova::Server', ret)
        self.assertIsInstance(yaml.safe_load(ret), dict)

    def test_heat_resource_template_fmt_arg_long_json(self):
        ret = self.heat('resource-template --format json OS::Nova::Server')
        self.assertIn('"Type": "OS::Nova::Server",', ret)
        self.assertIsInstance(json.loads(ret), dict)

    def test_heat_resource_type_list(self):
        ret = self.heat('resource-type-list')
        rsrc_types = self.parser.listing(ret)
        self.assertTableStruct(rsrc_types, ['resource_type'])

    def test_heat_resource_type_show(self):
        rsrc_schema = self.heat('resource-type-show OS::Nova::Server')
        # resource-type-show returns a json resource schema
        self.assertIsInstance(json.loads(rsrc_schema), dict)

    def test_heat_template_validate_yaml(self):
        filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                'heat_templates/heat_minimal.yaml')
        ret = self.heat('template-validate -f %s' % filepath)
        # On success template-validate returns a json representation
        # of the template parameters
        self.assertIsInstance(json.loads(ret), dict)

    def test_heat_template_validate_hot(self):
        filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                'heat_templates/heat_minimal_hot.yaml')
        ret = self.heat('template-validate -f %s' % filepath)
        self.assertIsInstance(json.loads(ret), dict)

    def test_heat_help(self):
        self.heat('help')

    def test_heat_help_cmd(self):
        # Check requesting help for a specific command works
        help_text = self.heat('help resource-template')
        lines = help_text.split('\n')
        self.assertFirstLineStartsWith(lines, 'usage: heat resource-template')

    def test_heat_version(self):
        self.heat('', flags='--version')
