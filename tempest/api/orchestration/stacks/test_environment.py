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

from tempest.api.orchestration import base
from tempest.common.utils import data_utils
from tempest import config
from tempest import test


CONF = config.CONF
LOG = logging.getLogger(__name__)


class StackEnvironmentTest(base.BaseOrchestrationTest):

    @test.attr(type='gate')
    def test_environment_parameter(self):
        """Test passing a stack parameter via the environment."""
        stack_name = data_utils.rand_name('heat')
        template = self.load_template('random_string')
        environment = {'parameters': {'random_length': 20}}

        stack_identifier = self.create_stack(stack_name, template,
                                             environment=environment)
        self.client.wait_for_stack_status(stack_identifier, 'CREATE_COMPLETE')

        random_len = self.get_stack_output(stack_identifier, 'random_length')
        self.assertEqual(20, random_len)

        random_value = self.get_stack_output(stack_identifier, 'random_value')
        self.assertEqual(20, len(random_value))
