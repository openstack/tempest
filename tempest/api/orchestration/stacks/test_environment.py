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

import logging

from tempest_lib.common.utils import data_utils

from tempest.api.orchestration import base
from tempest import config
from tempest import test


CONF = config.CONF
LOG = logging.getLogger(__name__)


class StackEnvironmentTest(base.BaseOrchestrationTest):

    @test.attr(type='gate')
    @test.idempotent_id('37d4346b-1abd-4442-b7b1-2a4e5749a1e3')
    def test_environment_parameter(self):
        """Test passing a stack parameter via the environment."""
        stack_name = data_utils.rand_name('heat')
        template = self.read_template('random_string')
        environment = {'parameters': {'random_length': 20}}

        stack_identifier = self.create_stack(stack_name, template,
                                             environment=environment)
        self.client.wait_for_stack_status(stack_identifier, 'CREATE_COMPLETE')

        random_len = self.get_stack_output(stack_identifier, 'random_length')
        self.assertEqual(20, random_len)

        random_value = self.get_stack_output(stack_identifier, 'random_value')
        self.assertEqual(20, len(random_value))

    @test.attr(type='gate')
    @test.idempotent_id('73bce717-ad22-4853-bbef-6ed89b632701')
    def test_environment_provider_resource(self):
        """Test passing resource_registry defining a provider resource."""
        stack_name = data_utils.rand_name('heat')
        template = '''
heat_template_version: 2013-05-23
resources:
  random:
    type: My:Random::String
outputs:
    random_value:
        value: {get_attr: [random, random_value]}
'''
        environment = {'resource_registry':
                       {'My:Random::String': 'my_random.yaml'}}
        files = {'my_random.yaml': self.read_template('random_string')}

        stack_identifier = self.create_stack(stack_name, template,
                                             environment=environment,
                                             files=files)
        self.client.wait_for_stack_status(stack_identifier, 'CREATE_COMPLETE')

        # random_string.yaml specifies a length of 10
        random_value = self.get_stack_output(stack_identifier, 'random_value')
        random_string_template = self.load_template('random_string')
        expected_length = random_string_template['parameters'][
            'random_length']['default']
        self.assertEqual(expected_length, len(random_value))

    @test.attr(type='gate')
    @test.idempotent_id('9d682e5a-f4bb-47d5-8472-9d3cacb855df')
    def test_files_provider_resource(self):
        """Test untyped defining of a provider resource via "files"."""
        # It's also possible to specify the filename directly in the template.
        # without adding the type alias to resource_registry
        stack_name = data_utils.rand_name('heat')
        template = '''
heat_template_version: 2013-05-23
resources:
  random:
    type: my_random.yaml
outputs:
    random_value:
        value: {get_attr: [random, random_value]}
'''
        files = {'my_random.yaml': self.read_template('random_string')}

        stack_identifier = self.create_stack(stack_name, template,
                                             files=files)
        self.client.wait_for_stack_status(stack_identifier, 'CREATE_COMPLETE')

        # random_string.yaml specifies a length of 10
        random_value = self.get_stack_output(stack_identifier, 'random_value')
        random_string_template = self.load_template('random_string')
        expected_length = random_string_template['parameters'][
            'random_length']['default']
        self.assertEqual(expected_length, len(random_value))
