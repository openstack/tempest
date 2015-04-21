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

from oslo_log import log as logging
from tempest_lib.common.utils import data_utils

from tempest.api.orchestration import base
from tempest import test


LOG = logging.getLogger(__name__)


class StacksTestJSON(base.BaseOrchestrationTest):
    empty_template = "HeatTemplateFormatVersion: '2012-12-12'\n"

    @classmethod
    def resource_setup(cls):
        super(StacksTestJSON, cls).resource_setup()

    @test.attr(type='smoke')
    @test.idempotent_id('d35d628c-07f6-4674-85a1-74db9919e986')
    def test_stack_list_responds(self):
        stacks = self.client.list_stacks()
        self.assertIsInstance(stacks, list)

    @test.attr(type='smoke')
    @test.idempotent_id('10498bd5-a83e-4b62-a817-ce24afe938fe')
    def test_stack_crud_no_resources(self):
        stack_name = data_utils.rand_name('heat')

        # create the stack
        stack_identifier = self.create_stack(
            stack_name, self.empty_template)
        stack_id = stack_identifier.split('/')[1]

        # wait for create complete (with no resources it should be instant)
        self.client.wait_for_stack_status(stack_identifier, 'CREATE_COMPLETE')

        # check for stack in list
        stacks = self.client.list_stacks()
        list_ids = list([stack['id'] for stack in stacks])
        self.assertIn(stack_id, list_ids)

        # fetch the stack
        stack = self.client.show_stack(stack_identifier)
        self.assertEqual('CREATE_COMPLETE', stack['stack_status'])

        # fetch the stack by name
        stack = self.client.show_stack(stack_name)
        self.assertEqual('CREATE_COMPLETE', stack['stack_status'])

        # fetch the stack by id
        stack = self.client.show_stack(stack_id)
        self.assertEqual('CREATE_COMPLETE', stack['stack_status'])

        # delete the stack
        self.client.delete_stack(stack_identifier)
        self.client.wait_for_stack_status(stack_identifier, 'DELETE_COMPLETE')
